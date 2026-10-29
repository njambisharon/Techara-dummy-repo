import uuid


def test_operator_can_get_business(
    client, operator, auth_headers, make_site, make_business
):
    site = make_site(org=operator.organisation, creator=operator)
    business = make_business(
        site=site,
        logger=operator,
        business_name="Mpanta Maize Mill",
    )

    response = client.get(
        f"/businesses/{business.business_id}",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["business_id"] == str(business.business_id)
    assert body["business_name"] == "Mpanta Maize Mill"
    assert body["site_id"] == str(site.site_id)


def test_get_business_hides_business_from_other_organisation(
    client, operator, auth_headers, make_site, make_business
):
    other_site = make_site()
    business = make_business(site=other_site)

    response = client.get(
        f"/businesses/{business.business_id}",
        headers=auth_headers(operator),
    )

    assert response.status_code == 404


def test_get_business_returns_404_for_unknown_id(
    client, operator, auth_headers
):
    response = client.get(
        f"/businesses/{uuid.uuid4()}",
        headers=auth_headers(operator),
    )

    assert response.status_code == 404


def test_get_business_requires_authentication(client):
    response = client.get(f"/businesses/{uuid.uuid4()}")
    assert response.status_code == 401


def test_operator_can_patch_business_fields(
    client, operator, auth_headers, make_site, make_business
):
    site = make_site(org=operator.organisation, creator=operator)
    business = make_business(
        site=site,
        logger=operator,
        business_name="Old Business Name",
    )

    response = client.patch(
        f"/businesses/{business.business_id}",
        json={"business_name": "Updated Business Name"},
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["business_name"] == "Updated Business Name"
    assert body["business_id"] == str(business.business_id)
    assert body["site_id"] == str(site.site_id)


def test_patch_business_hides_business_from_other_organisation(
    client, operator, auth_headers, make_site, make_business
):
    other_site = make_site()
    business = make_business(site=other_site)

    response = client.patch(
        f"/businesses/{business.business_id}",
        json={"business_name": "Should Not Change"},
        headers=auth_headers(operator),
    )

    assert response.status_code == 404
    assert business.business_name != "Should Not Change"


def test_patch_business_rejects_invalid_days_per_month(
    client, operator, auth_headers, make_site, make_business
):
    site = make_site(org=operator.organisation, creator=operator)
    business = make_business(site=site, logger=operator)

    response = client.patch(
        f"/businesses/{business.business_id}",
        json={"days_per_month": 32},
        headers=auth_headers(operator),
    )

    assert response.status_code == 422


def test_patch_business_requires_authentication(client):
    response = client.patch(
        f"/businesses/{uuid.uuid4()}",
        json={"business_name": "No Auth"},
    )
    assert response.status_code == 401
