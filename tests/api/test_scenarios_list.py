import uuid
from datetime import timedelta
from decimal import Decimal

from models.enums import StartupDataLabel
from models.scenario import Scenario

STARTUP = {
    "startup_power_kw": Decimal("5.00"),
    "startup_duration_s": 3,
    "startup_data_label": StartupDataLabel.USER_ENTERED,
}


def test_scenarios_are_ranked(
    client, operator, auth_headers, run_scenario, scenario_site, metered_business
):
    small = metered_business(scenario_site.site, kw="1000", **STARTUP)
    bigger = metered_business(scenario_site.site, kw="3000", **STARTUP)
    too_big = metered_business(scenario_site.site, kw="12000", **STARTUP)
    no_startup = metered_business(scenario_site.site, kw="1000")
    for business in (small, too_big, no_startup, bigger):
        assert run_scenario(scenario_site, [business]).status_code == 201
    response = client.get("/scenarios", headers=auth_headers(operator))
    assert response.status_code == 200
    body = response.json()
    assert [item["rank"] for item in body] == [1, 2, 3, 4]
    assert [item["businesses"][0]["business_id"] for item in body] == [
        str(bigger.business_id),
        str(small.business_id),
        str(no_startup.business_id),
        str(too_big.business_id),
    ]


def test_newest_order_keeps_ranks(
    client,
    db_session,
    operator,
    auth_headers,
    run_scenario,
    scenario_site,
    metered_business,
):
    first = metered_business(scenario_site.site, kw="1000", **STARTUP)
    second = metered_business(scenario_site.site, kw="12000", **STARTUP)
    older = run_scenario(scenario_site, [first]).json()
    run_scenario(scenario_site, [second])
    saved = db_session.get(Scenario, uuid.UUID(older["scenario_id"]))
    saved.created_at = saved.created_at - timedelta(hours=1)
    db_session.flush()
    body = client.get("/scenarios?order=newest", headers=auth_headers(operator)).json()
    assert body[0]["businesses"][0]["business_id"] == str(second.business_id)
    assert body[0]["rank"] == 2


def test_filter_by_business(
    client, operator, auth_headers, run_scenario, scenario_site, metered_business
):
    one = metered_business(scenario_site.site, **STARTUP)
    two = metered_business(scenario_site.site, **STARTUP)
    run_scenario(scenario_site, [one])
    run_scenario(scenario_site, [two])
    body = client.get(
        f"/scenarios?business_id={one.business_id}", headers=auth_headers(operator)
    ).json()
    assert len(body) == 1


def test_filter_by_site(
    client,
    operator,
    auth_headers,
    run_scenario,
    scenario_site,
    make_scenario_site,
    metered_business,
):
    other = make_scenario_site()
    business = metered_business(scenario_site.site, **STARTUP)
    run_scenario(scenario_site, [business])
    run_scenario(other, [business])
    body = client.get(
        f"/scenarios?site_id={other.site_id}", headers=auth_headers(operator)
    ).json()
    assert len(body) == 1
    assert body[0]["site_id"] == str(other.site_id)


def test_other_organisation_scenarios_are_hidden(
    client, operator, auth_headers, make_scenario
):
    make_scenario()
    assert client.get("/scenarios", headers=auth_headers(operator)).json() == []


def test_field_agent_cannot_list_scenarios(client, field_agent, auth_headers):
    assert (
        client.get("/scenarios", headers=auth_headers(field_agent)).status_code == 403
    )
