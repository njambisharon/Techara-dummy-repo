import uuid

from models.business import Business
from models.enums import BusinessType


def test_operator_can_create_business(
    client, db_session, operator, auth_headers, make_site
):
    site = make_site(org=operator.organisation, creator=operator)

    response = client.post(
        "/businesses",
        json={
            "site_id": str(site.site_id),
            "business_name": "Mpanta Maize Mill",
            "business_type": BusinessType.MAIZE_MILL.value,
            "owner_first_name": "John",
            "owner_last_name": "Banda",
            "owner_phone": "+260977123456",
            "operating_hours": {"start": "08:00", "end": "17:00"},
            "days_per_month": 25,
        },
        headers=auth_headers(operator),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["site_id"] == str(site.site_id)
    assert body["logged_by"] == str(operator.user_id)
    assert body["business_name"] == "Mpanta Maize Mill"

    business = db_session.get(Business, uuid.UUID(body["business_id"]))

    assert business is not None
    assert business.site_id == site.site_id
    assert business.logged_by == operator.user_id


def test_business_create_rejects_site_from_other_organisation(
    client, operator, auth_headers, make_site
):
    other_site = make_site()

    response = client.post(
        "/businesses",
        json={
            "site_id": str(other_site.site_id),
            "business_name": "Other Organisation Business",
            "business_type": BusinessType.RETAIL.value,
            "owner_first_name": "John",
            "owner_last_name": "Banda",
            "operating_hours": {"start": "08:00", "end": "17:00"},
            "days_per_month": 25,
        },
        headers=auth_headers(operator),
    )

    assert response.status_code == 404


def test_business_create_requires_auth(client, make_site):
    site = make_site()

    response = client.post(
        "/businesses",
        json={
            "site_id": str(site.site_id),
            "business_name": "Unauthorised Business",
            "business_type": BusinessType.RETAIL.value,
            "owner_first_name": "John",
            "owner_last_name": "Banda",
            "operating_hours": {"start": "08:00", "end": "17:00"},
            "days_per_month": 25,
        },
    )

    assert response.status_code == 401


def test_business_create_rejects_invalid_site_id(client, operator, auth_headers):
    response = client.post(
        "/businesses",
        json={
            "site_id": "not-a-uuid",
            "business_name": "Invalid Site Business",
            "business_type": BusinessType.RETAIL.value,
            "owner_first_name": "John",
            "owner_last_name": "Banda",
            "operating_hours": {"start": "08:00", "end": "17:00"},
            "days_per_month": 25,
        },
        headers=auth_headers(operator),
    )

    assert response.status_code == 422


def test_business_create_rejects_invalid_days_per_month(
    client, operator, auth_headers, make_site
):
    site = make_site(org=operator.organisation, creator=operator)

    response = client.post(
        "/businesses",
        json={
            "site_id": str(site.site_id),
            "business_name": "Invalid Days Business",
            "business_type": BusinessType.RETAIL.value,
            "owner_first_name": "John",
            "owner_last_name": "Banda",
            "operating_hours": {"start": "08:00", "end": "17:00"},
            "days_per_month": 32,
        },
        headers=auth_headers(operator),
    )

    assert response.status_code == 422
