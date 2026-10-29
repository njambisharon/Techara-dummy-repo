def test_list_returns_only_own_organisation_sites(
    client, operator, auth_headers, make_site
):
    make_site(org=operator.organisation, creator=operator, name="Bravo")
    make_site(org=operator.organisation, creator=operator, name="Alpha")
    make_site(name="Other org site")
    response = client.get("/sites", headers=auth_headers(operator))
    assert response.status_code == 200
    assert [site["site_name"] for site in response.json()] == ["Alpha", "Bravo"]


def test_field_agent_can_list_sites(
    client, field_agent, operator, auth_headers, make_site
):
    make_site(org=operator.organisation, creator=operator)
    response = client.get("/sites", headers=auth_headers(field_agent))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_is_empty_for_new_organisation(client, operator, auth_headers):
    response = client.get("/sites", headers=auth_headers(operator))
    assert response.json() == []


def test_list_sites_requires_auth(client):
    assert client.get("/sites").status_code == 401
