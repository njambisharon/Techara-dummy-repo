import uuid

from models.site import Site


def test_operator_can_create_site(client, db_session, operator, auth_headers):
    response = client.post(
        "/sites",
        json={"site_name": "Mpanta", "district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["site_name"] == "Mpanta"
    assert body["organisation_id"] == str(operator.organisation_id)
    assert body["created_by"] == str(operator.user_id)
    assert db_session.get(Site, uuid.UUID(body["site_id"])) is not None


def test_site_name_is_trimmed(client, operator, auth_headers):
    response = client.post(
        "/sites",
        json={"site_name": "  Mpanta  ", "district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.json()["site_name"] == "Mpanta"


def test_duplicate_site_name_in_same_org_returns_409(
    client, operator, auth_headers, make_site
):
    make_site(org=operator.organisation, creator=operator, name="Mpanta")
    response = client.post(
        "/sites",
        json={"site_name": "Mpanta", "district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 409


def test_same_site_name_allowed_in_other_org(client, operator, auth_headers, make_site):
    make_site(name="Mpanta")
    response = client.post(
        "/sites",
        json={"site_name": "Mpanta", "district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 201


def test_blank_site_name_returns_422(client, operator, auth_headers):
    response = client.post(
        "/sites",
        json={"site_name": "   ", "district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 422


def test_field_agent_cannot_create_site(client, field_agent, auth_headers):
    response = client.post(
        "/sites",
        json={"site_name": "Mpanta", "district": "Samfya"},
        headers=auth_headers(field_agent),
    )
    assert response.status_code == 403


def test_create_site_requires_auth(client):
    response = client.post("/sites", json={"site_name": "Mpanta", "district": "Samfya"})
    assert response.status_code == 401
