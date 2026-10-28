import uuid


def test_rename_scenario(client, operator, auth_headers, saved_scenario):
    url = f"/scenarios/{saved_scenario['scenario_id']}"
    response = client.patch(
        url, json={"name": "Chanda mill, dry season"}, headers=auth_headers(operator)
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Chanda mill, dry season"
    assert client.get(url, headers=auth_headers(operator)).json()["name"] == (
        "Chanda mill, dry season"
    )


def test_rename_keeps_the_result(client, operator, auth_headers, saved_scenario):
    body = client.patch(
        f"/scenarios/{saved_scenario['scenario_id']}",
        json={"name": "Renamed"},
        headers=auth_headers(operator),
    ).json()
    assert body["outcome"] == saved_scenario["outcome"]
    assert body["check_results"] == saved_scenario["check_results"]


def test_name_too_long_returns_422(client, operator, auth_headers, saved_scenario):
    response = client.patch(
        f"/scenarios/{saved_scenario['scenario_id']}",
        json={"name": "x" * 101},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_rename_unknown_scenario_returns_404(client, operator, auth_headers):
    response = client.patch(
        f"/scenarios/{uuid.uuid4()}", json={"name": "x"}, headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_rename_other_organisation_scenario_returns_404(
    client, operator, auth_headers, make_scenario
):
    other = make_scenario()
    response = client.patch(
        f"/scenarios/{other.scenario_id}",
        json={"name": "x"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 404


def test_field_agent_cannot_rename(client, field_agent, auth_headers):
    response = client.patch(
        f"/scenarios/{uuid.uuid4()}",
        json={"name": "x"},
        headers=auth_headers(field_agent),
    )
    assert response.status_code == 403
