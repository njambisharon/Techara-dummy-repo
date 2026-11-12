from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture
def own_site(make_site, operator):
    return make_site(org=operator.organisation, creator=operator)


def build_csv(days=3, low_day=1, utc=True):
    start = datetime(2026, 10, 1, tzinfo=UTC) - timedelta(hours=2)
    lines = ["timestamp,load_kw,solar_kw"]
    for step in range(days * 24):
        moment = start + timedelta(hours=step)
        local_hour = (moment.hour + 2) % 24
        solar = 10.0 if 7 <= local_hour < 17 else 0.0
        if step // 24 == low_day:
            solar = solar / 2
        stamp = (
            moment.isoformat()
            if utc
            else (moment + timedelta(hours=2)).replace(tzinfo=None).isoformat()
        )
        lines.append(f"{stamp},{3.0 if local_hour >= 18 else 1.0},{solar}")
    return "\n".join(lines)


def test_import_averages_into_local_hours(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv()},
        headers=auth_headers(operator),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["baseline_demand_kw"][19] == 3.0
    assert body["baseline_demand_kw"][10] == 1.0
    assert body["solar_profile"]["low_sun_kw"][10] == 5.0
    assert body["low_sun_date"] == "2026-10-02"
    assert body["complete_days"] == 3
    assert body["suggested_settings"]["min_observed_days"] == 1


def test_naive_timestamps_use_source_timezone(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv(utc=False), "source_timezone": "Africa/Lusaka"},
        headers=auth_headers(operator),
    )
    assert response.json()["baseline_demand_kw"][19] == 3.0


def test_import_does_not_save_a_profile(client, operator, auth_headers, own_site):
    client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv()},
        headers=auth_headers(operator),
    )
    assert (
        client.get(
            f"/sites/{own_site.site_id}/profiles", headers=auth_headers(operator)
        ).json()
        == []
    )


def test_missing_columns_returns_422(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": "time,watts\n2026-10-01T00:00:00,5"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_no_full_day_returns_422(client, operator, auth_headers, own_site):
    short = "\n".join(build_csv().splitlines()[:10])
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": short},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_unknown_timezone_returns_422(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv(), "source_timezone": "Mars/Olympus"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_field_agent_cannot_import(client, field_agent, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv()},
        headers=auth_headers(field_agent),
    )
    assert response.status_code == 403


def test_column_map_reads_custom_headers(client, operator, auth_headers, own_site):
    csv_text = build_csv().replace("timestamp,load_kw,solar_kw", "Time,Use,PV", 1)
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={
            "csv_text": csv_text,
            "column_map": {"timestamp": "Time", "load_kw": "Use", "solar_kw": "PV"},
        },
        headers=auth_headers(operator),
    )
    assert response.status_code == 200
    assert response.json()["baseline_demand_kw"][19] == 3.0


def test_column_map_with_unknown_column_returns_422(
    client, operator, auth_headers, own_site
):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={
            "csv_text": build_csv(),
            "column_map": {
                "timestamp": "timestamp",
                "load_kw": "Missing",
                "solar_kw": "solar_kw",
            },
        },
        headers=auth_headers(operator),
    )
    assert response.status_code == 422
    assert "Missing" in response.json()["detail"]


def test_non_finite_rows_are_skipped(client, operator, auth_headers, own_site):
    csv_text = build_csv() + "\n2026-10-05T00:00:00+00:00,nan,1.0"
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": csv_text},
        headers=auth_headers(operator),
    )
    assert response.status_code == 200
    assert response.json()["rows_skipped"] == 1


def test_enough_days_suggest_observed_labels(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv(days=3)},
        headers=auth_headers(operator),
    )
    labels = response.json()["suggested_data_labels"]
    assert labels["baseline"] == "observed"
    assert labels["solar"] == "observed"


def test_two_days_suggest_observed_labels(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": build_csv(days=2)},
        headers=auth_headers(operator),
    )
    labels = response.json()["suggested_data_labels"]
    assert labels["baseline"] == "observed"
    assert labels["solar"] == "observed"
    assert labels["battery"] == "user_entered"


def test_bad_timestamps_show_the_first_skipped_row(
    client, operator, auth_headers, own_site
):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": "timestamp,load_kw,solar_kw\n01/10/2026 00:00,1.0,1.0"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422
    assert "01/10/2026 00:00" in response.json()["detail"]


def test_oversized_csv_returns_422(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import",
        json={"csv_text": "a" * 10_000_001},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_cannot_import_for_other_organisation_site(
    client, operator, auth_headers, make_site
):
    other_site = make_site()
    response = client.post(
        f"/sites/{other_site.site_id}/profiles/import",
        json={"csv_text": build_csv()},
        headers=auth_headers(operator),
    )
    assert response.status_code == 404


def test_import_needs_a_token(client, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles/import", json={"csv_text": build_csv()}
    )
    assert response.status_code == 401
