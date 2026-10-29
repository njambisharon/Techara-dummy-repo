from decimal import Decimal

import pytest
from models.enums import StartupDataLabel

STARTUP = {
    "startup_power_kw": Decimal("5.00"),
    "startup_duration_s": 3,
    "startup_data_label": StartupDataLabel.USER_ENTERED,
}


@pytest.fixture
def mill(scenario_site, metered_business):
    return metered_business(
        scenario_site.site, business_name="Chanda Milling", **STARTUP
    )


def test_small_daytime_business_is_feasible(run_scenario, scenario_site, mill):
    response = run_scenario(scenario_site, [mill])
    assert response.status_code == 201
    body = response.json()
    assert body["outcome"] == "feasible"
    assert body["data_label"] == "estimated"
    assert body["site_name"] == scenario_site.site.site_name
    assert body["profile_version"] == 1
    assert body["businesses"][0]["business_name"] == "Chanda Milling"
    assert body["businesses"][0]["decision"] is None
    assert set(body["check_results"]) >= {"power", "startup", "energy", "battery"}
    assert body["revenue_basis"] == "planned"
    assert Decimal(body["monthly_revenue"]) == Decimal("1170.00")
    assert len(body["simulation_trace"]["with_new"]["stored_kwh"]) == 48


def test_snapshot_keeps_profiles_but_no_owner_details(
    run_scenario, scenario_site, mill
):
    snapshot = run_scenario(scenario_site, [mill]).json()["input_snapshot"]
    business = snapshot["businesses"][0]
    assert business["average_kw"][9] == 2.0
    assert business["observed_days"] == 3
    assert "owner_first_name" not in business
    assert "owner_phone" not in str(snapshot)


def test_too_big_business_is_not_feasible(
    run_scenario, scenario_site, metered_business
):
    welder = metered_business(scenario_site.site, kw="12000", **STARTUP)
    body = run_scenario(scenario_site, [welder]).json()
    assert body["outcome"] == "not_feasible"
    assert body["check_results"]["power"]["status"] == "fail"
    assert body["check_results"]["power"]["causing_business_ids"] == [
        str(welder.business_id)
    ]


def test_missing_startup_data_is_conditional(
    run_scenario, scenario_site, metered_business
):
    salon = metered_business(scenario_site.site)
    body = run_scenario(scenario_site, [salon]).json()
    assert body["outcome"] == "conditionally_feasible"
    assert body["check_results"]["startup"]["status"] == "unknown"


def test_business_at_another_site_is_flagged(
    run_scenario, scenario_site, metered_business, make_site, operator
):
    other_site = make_site(org=operator.organisation, creator=operator)
    business = metered_business(other_site, **STARTUP)
    flags = run_scenario(scenario_site, [business]).json()["check_results"]["flags"]
    assert flags[0]["type"] == "not_nearest_site"


def test_too_few_observed_days_returns_422(
    run_scenario, scenario_site, metered_business
):
    fresh = metered_business(scenario_site.site, days=1, **STARTUP)
    assert run_scenario(scenario_site, [fresh]).status_code == 422


def test_initial_stored_outside_soc_limits_returns_422(
    run_scenario, scenario_site, mill
):
    assert (
        run_scenario(scenario_site, [mill], initial_stored_kwh="39.00").status_code
        == 422
    )


def test_same_business_twice_returns_422(run_scenario, scenario_site, mill):
    assert run_scenario(scenario_site, [mill, mill]).status_code == 422


def test_other_organisation_profile_returns_404(run_scenario, make_site_profile, mill):
    assert run_scenario(make_site_profile(), [mill]).status_code == 404


def test_other_organisation_business_returns_404(
    run_scenario, scenario_site, make_business
):
    assert run_scenario(scenario_site, [make_business()]).status_code == 404


def test_field_agent_cannot_run_scenarios(
    client, field_agent, auth_headers, scenario_site, mill
):
    payload = {
        "profile_id": str(scenario_site.profile_id),
        "initial_stored_kwh": "20.00",
        "business_ids": [str(mill.business_id)],
    }
    assert (
        client.post(
            "/scenarios", json=payload, headers=auth_headers(field_agent)
        ).status_code
        == 403
    )
