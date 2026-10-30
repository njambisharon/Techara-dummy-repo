def test_operator_can_update_district(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator, name="Mpanta")
    response = client.patch(
        f"/sites/{site.site_id}",
        json={"district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 200
    assert response.json()["district"] == "Samfya"
    assert response.json()["site_name"] == "Mpanta"


def test_rename_to_existing_name_returns_409(client, operator, auth_headers, make_site):
    make_site(org=operator.organisation, creator=operator, name="Alpha")
    site = make_site(org=operator.organisation, creator=operator, name="Bravo")
    response = client.patch(
        f"/sites/{site.site_id}",
        json={"site_name": "Alpha"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 409


def test_rename_to_same_name_is_allowed(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator, name="Alpha")
    response = client.patch(
        f"/sites/{site.site_id}",
        json={"site_name": "Alpha"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 200


def test_empty_district_returns_422(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.patch(
        f"/sites/{site.site_id}", json={"district": ""}, headers=auth_headers(operator)
    )
    assert response.status_code == 422


def test_field_agent_cannot_update_site(
    client, field_agent, operator, auth_headers, make_site
):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.patch(
        f"/sites/{site.site_id}",
        json={"district": "Samfya"},
        headers=auth_headers(field_agent),
    )
    assert response.status_code == 403


def test_cannot_update_other_organisation_site(
    client, operator, auth_headers, make_site
):
    other_site = make_site()
    response = client.patch(
        f"/sites/{other_site.site_id}",
        json={"district": "Samfya"},
        headers=auth_headers(operator),
    )
    assert response.status_code == 404
