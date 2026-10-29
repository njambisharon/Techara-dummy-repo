from decimal import Decimal

import pytest
from models.enums import StartupDataLabel

STARTUP = {
    "startup_power_kw": Decimal("5.00"),
    "startup_duration_s": 3,
    "startup_data_label": StartupDataLabel.USER_ENTERED,
}


@pytest.fixture
def compare(client, auth_headers, operator):
    def factory(sites, businesses, user=None, **overrides):
        payload = {
            "site_ids": [str(site.site_id) for site in sites],
            "business_ids": [str(business.business_id) for business in businesses],
            "solar_day_type": "average",
            "period_days": 2,
        }
        payload.update(overrides)
        return client.post(
            "/scenarios/compare-sites",
            json=payload,
            headers=auth_headers(user or operator),
        )

    return factory


def test_compare_ranks_every_site(
    compare, scenario_site, make_scenario_site, metered_business
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    response = compare([scenario_site, other], [business])
    assert response.status_code == 201
    body = response.json()
    assert [item["rank"] for item in body] == [1, 2]
    assert {item["site_id"] for item in body} == {
        str(scenario_site.site_id),
        str(other.site_id),
    }


def test_compare_saves_one_scenario_per_site(
    client,
    operator,
    auth_headers,
    compare,
    scenario_site,
    make_scenario_site,
    metered_business,
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    compare([scenario_site, other], [business])
    assert len(client.get("/scenarios", headers=auth_headers(operator)).json()) == 2


def test_compare_flags_business_from_another_site(
    client,
    operator,
    auth_headers,
    compare,
    scenario_site,
    make_scenario_site,
    metered_business,
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    body = compare([scenario_site, other], [business]).json()
    away = next(item for item in body if item["site_id"] == str(other.site_id))
    detail = client.get(
        f"/scenarios/{away['scenario_id']}", headers=auth_headers(operator)
    ).json()
    assert detail["check_results"]["flags"][0]["type"] == "not_nearest_site"


def test_same_site_twice_returns_422(compare, scenario_site, metered_business):
    business = metered_business(scenario_site.site, **STARTUP)
    assert compare([scenario_site, scenario_site], [business]).status_code == 422


def test_one_site_is_not_a_comparison(compare, scenario_site, metered_business):
    business = metered_business(scenario_site.site, **STARTUP)
    assert compare([scenario_site], [business]).status_code == 422


def test_soc_outside_limits_returns_422(
    compare, scenario_site, make_scenario_site, metered_business
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    response = compare([scenario_site, other], [business], initial_soc_percent="0.00")
    assert response.status_code == 422


def test_site_without_profile_returns_404(
    compare, scenario_site, make_site, operator, metered_business
):
    bare = make_site(org=operator.organisation, creator=operator)
    business = metered_business(scenario_site.site, **STARTUP)
    assert compare([scenario_site, bare], [business]).status_code == 404


def test_other_organisation_site_returns_404(
    compare, scenario_site, make_site_profile, metered_business
):
    foreign = make_site_profile()
    business = metered_business(scenario_site.site, **STARTUP)
    assert compare([scenario_site, foreign], [business]).status_code == 404


def test_field_agent_cannot_compare(
    compare, field_agent, scenario_site, make_scenario_site, metered_business
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    response = compare([scenario_site, other], [business], user=field_agent)
    assert response.status_code == 403
