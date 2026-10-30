from datetime import datetime, timezone
from decimal import Decimal


def test_business_profile_aggregates_readings_by_hour(
    client,
    operator,
    auth_headers,
    make_site,
    make_business,
    make_assignment,
    make_reading,
):
    site = make_site(org=operator.organisation, creator=operator)
    business = make_business(site=site, logger=operator)
    assignment = make_assignment(business=business)

    make_reading(
        assignment=assignment,
        measured_at=datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
        power_w=Decimal("1000.00"),
    )
    make_reading(
        assignment=assignment,
        measured_at=datetime(2026, 1, 1, 10, 35, tzinfo=timezone.utc),
        power_w=Decimal("3000.00"),
    )
    make_reading(
        assignment=assignment,
        measured_at=datetime(2026, 1, 1, 11, 10, tzinfo=timezone.utc),
        power_w=Decimal("500.00"),
    )

    response = client.get(
        f"/businesses/{business.business_id}/profile",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["business_id"] == str(business.business_id)
    assert len(body["hours"]) == 24

    by_hour = {item["hour"]: item for item in body["hours"]}
    assert by_hour[12]["average_power_kw"] == 2.0
    assert by_hour[12]["peak_power_kw"] == 3.0
    assert by_hour[12]["reading_count"] == 2
    assert by_hour[13]["average_power_kw"] == 0.5
    assert by_hour[13]["peak_power_kw"] == 0.5
    assert by_hour[13]["reading_count"] == 1


def test_business_profile_returns_empty_hours_as_null(
    client, operator, auth_headers, make_site, make_business
):
    site = make_site(org=operator.organisation, creator=operator)
    business = make_business(site=site, logger=operator)

    response = client.get(
        f"/businesses/{business.business_id}/profile",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["hours"]) == 24
    assert all(item["average_power_kw"] is None for item in body["hours"])
    assert all(item["reading_count"] == 0 for item in body["hours"])


def test_business_profile_hides_other_organisation_business(
    client,
    operator,
    auth_headers,
    make_site,
    make_business,
    make_assignment,
    make_reading,
):
    other_site = make_site()
    business = make_business(site=other_site)
    assignment = make_assignment(business=business)
    make_reading(assignment=assignment, power_w=Decimal("2500.00"))

    response = client.get(
        f"/businesses/{business.business_id}/profile",
        headers=auth_headers(operator),
    )

    assert response.status_code == 404


def test_business_profile_requires_authentication(client):
    import uuid

    response = client.get(f"/businesses/{uuid.uuid4()}/profile")
    assert response.status_code == 401
