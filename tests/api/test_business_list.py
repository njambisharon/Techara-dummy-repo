
def test_operator_can_list_businesses_in_own_organisation(
    client, operator, auth_headers, make_site, make_business
):
    site = make_site(org=operator.organisation, creator=operator)
    business_b = make_business(
        site=site,
        logger=operator,
        business_name="Zambezi Milling",
    )
    business_a = make_business(
        site=site,
        logger=operator,
        business_name="Chongwe Retail",
    )

    response = client.get(
        "/businesses",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2
    assert [item["business_name"] for item in body] == [
        "Chongwe Retail",
        "Zambezi Milling",
    ]
    assert {item["business_id"] for item in body} == {
        str(business_a.business_id),
        str(business_b.business_id),
    }


def test_business_list_excludes_other_organisations(
    client, operator, auth_headers, make_site, make_business
):
    own_site = make_site(org=operator.organisation, creator=operator)
    own_business = make_business(
        site=own_site,
        logger=operator,
        business_name="My Organisation Business",
    )

    other_site = make_site()
    make_business(
        site=other_site,
        business_name="Another Organisation Business",
    )

    response = client.get(
        "/businesses",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    body = response.json()

    assert len(body) == 1
    assert body[0]["business_id"] == str(own_business.business_id)
    assert body[0]["business_name"] == "My Organisation Business"


def test_business_list_returns_empty_list_when_no_businesses(
    client, operator, auth_headers
):
    response = client.get(
        "/businesses",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_business_list_requires_authentication(client):
    response = client.get("/businesses")

    assert response.status_code == 401
