import uuid


def test_get_scenario_returns_full_detail(
    client, operator, auth_headers, saved_scenario, scenario_site
):
    response = client.get(
        f"/scenarios/{saved_scenario['scenario_id']}", headers=auth_headers(operator)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scenario_id"] == saved_scenario["scenario_id"]
    assert body["outcome"] == saved_scenario["outcome"]
    assert set(body["check_results"]) >= {"power", "startup", "energy", "battery"}
    assert body["input_snapshot"]["profile_id"] == str(scenario_site.profile_id)
    assert "simulation_trace" in body


def test_unknown_scenario_returns_404(client, operator, auth_headers):
    response = client.get(f"/scenarios/{uuid.uuid4()}", headers=auth_headers(operator))
    assert response.status_code == 404


def test_other_organisation_scenario_returns_404(
    client, operator, auth_headers, make_scenario
):
    other = make_scenario()
    response = client.get(
        f"/scenarios/{other.scenario_id}", headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_field_agent_cannot_open_scenario(client, field_agent, auth_headers):
    response = client.get(
        f"/scenarios/{uuid.uuid4()}", headers=auth_headers(field_agent)
    )
    assert response.status_code == 403
