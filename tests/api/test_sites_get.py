import uuid


def test_get_site_returns_site(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.get(f"/sites/{site.site_id}", headers=auth_headers(operator))
    assert response.status_code == 200
    assert response.json()["site_id"] == str(site.site_id)


def test_site_from_other_organisation_returns_404(
    client, operator, auth_headers, make_site
):
    other_site = make_site()
    response = client.get(
        f"/sites/{other_site.site_id}", headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_unknown_site_returns_404(client, operator, auth_headers):
    response = client.get(f"/sites/{uuid.uuid4()}", headers=auth_headers(operator))
    assert response.status_code == 404


def test_invalid_site_id_returns_422(client, operator, auth_headers):
    response = client.get("/sites/not-a-uuid", headers=auth_headers(operator))
    assert response.status_code == 422
