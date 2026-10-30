import json

import pytest


def profile_payload(**overrides):
    payload = {
        "inverter_continuous_kw": "10.00",
        "inverter_surge_kw": "15.00",
        "inverter_surge_duration_s": 10,
        "battery_nominal_kwh": "40.00",
        "soc_min_percent": "20.00",
        "soc_max_percent": "90.00",
        "charge_efficiency": "0.950",
        "discharge_efficiency": "0.950",
        "max_charge_kw": "8.00",
        "max_discharge_kw": "8.00",
        "tariff_per_kwh": "2.50",
        "baseline_demand_kw": [0.5] * 24,
        "solar_profile": {"average_kw": [5.0] * 24, "low_sun_kw": [2.0] * 24},
        "settings": {
            "reserve_factor": 0.2,
            "safety_margin": 0.1,
            "unserved_energy_tolerance_kwh": 0.5,
            "night_start_hour": 18,
            "night_end_hour": 6,
            "min_observed_days": 3,
        },
        "data_labels": {
            "baseline": "estimated",
            "solar": "estimated",
            "battery": "user_entered",
        },
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def own_site(make_site, operator):
    return make_site(org=operator.organisation, creator=operator)


def test_first_profile_is_version_one(client, operator, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        json=profile_payload(),
        headers=auth_headers(operator),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["version"] == 1
    assert body["site_id"] == str(own_site.site_id)
    assert body["solar_profile"]["low_sun_kw"] == [2.0] * 24
    assert body["data_labels"]["solar"] == "estimated"
    assert body["settings"]["min_observed_days"] == 3


def test_next_profile_bumps_version(
    client, operator, auth_headers, own_site, make_site_profile
):
    make_site_profile(site=own_site, creator=operator, version=1)
    make_site_profile(site=own_site, creator=operator, version=2)
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        json=profile_payload(),
        headers=auth_headers(operator),
    )
    assert response.json()["version"] == 3


def test_inverter_fields_are_optional(client, operator, auth_headers, own_site):
    payload = profile_payload()
    for field in (
        "inverter_continuous_kw",
        "inverter_surge_kw",
        "inverter_surge_duration_s",
    ):
        payload.pop(field)
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        json=payload,
        headers=auth_headers(operator),
    )
    assert response.status_code == 201
    assert response.json()["inverter_surge_kw"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"soc_min_percent": "90.00", "soc_max_percent": "80.00"},
        {"charge_efficiency": "1.100"},
        {"tariff_per_kwh": "-1.00"},
        {"battery_nominal_kwh": "0"},
        {"baseline_demand_kw": [0.5] * 23},
        {"baseline_demand_kw": [-0.5] + [0.5] * 23},
        {"inverter_continuous_kw": "10.00", "inverter_surge_kw": "5.00"},
        {"solar_profile": {"average_kw": [5.0] * 24}},
        {
            "data_labels": {
                "baseline": "guessed",
                "solar": "estimated",
                "battery": "estimated",
            }
        },
        {"data_labels": {"baseline": "estimated", "battery": "user_entered"}},
        {"settings": {"min_observed_days": 3}},
    ],
)
def test_invalid_profile_returns_422(
    client, operator, auth_headers, own_site, overrides
):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        json=profile_payload(**overrides),
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_field_agent_cannot_create_profile(client, field_agent, auth_headers, own_site):
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        json=profile_payload(),
        headers=auth_headers(field_agent),
    )
    assert response.status_code == 403


def test_cannot_add_profile_to_other_organisation_site(
    client, operator, auth_headers, make_site
):
    other_site = make_site()
    response = client.post(
        f"/sites/{other_site.site_id}/profiles",
        json=profile_payload(),
        headers=auth_headers(operator),
    )
    assert response.status_code == 404


def test_nan_in_hourly_values_returns_422(client, operator, auth_headers, own_site):
    body = json.dumps(profile_payload()).replace("[0.5,", "[NaN,", 1)
    assert "NaN" in body
    response = client.post(
        f"/sites/{own_site.site_id}/profiles",
        content=body,
        headers={**auth_headers(operator), "Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_saving_again_leaves_the_old_version_unchanged(
    client, operator, auth_headers, own_site
):
    url = f"/sites/{own_site.site_id}/profiles"
    first = client.post(url, json=profile_payload(), headers=auth_headers(operator))
    client.post(
        url,
        json=profile_payload(tariff_per_kwh="3.00"),
        headers=auth_headers(operator),
    )
    versions = client.get(url, headers=auth_headers(operator)).json()
    assert [item["version"] for item in versions] == [2, 1]
    assert versions[1] == first.json()
    assert versions[0]["tariff_per_kwh"] != versions[1]["tariff_per_kwh"]


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_profiles_cannot_be_edited_or_deleted(
    client, operator, auth_headers, own_site, method
):
    response = getattr(client, method)(
        f"/sites/{own_site.site_id}/profiles", headers=auth_headers(operator)
    )
    assert response.status_code == 405
