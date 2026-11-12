def test_spare_capacity_uses_latest_profile(
    client, operator, auth_headers, make_site, make_site_profile
):
    site = make_site(org=operator.organisation, creator=operator)
    make_site_profile(site=site, creator=operator, version=1)
    newest = make_site_profile(site=site, creator=operator, version=2)
    response = client.get(
        f"/sites/{site.site_id}/spare-capacity", headers=auth_headers(operator)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"] == str(newest.profile_id)
    assert body["hourly_inverter_headroom_kw"][0] == 9.5
    assert body["usable_battery_kwh"] == 28.0
    assert set(body["days"]) == {"average", "low_sun"}
    assert body["days"]["average"]["hourly_solar_surplus_kw"][12] == 4.5


def test_missing_inverter_rating_gives_no_headroom(
    client, db_session, operator, auth_headers, make_site, make_site_profile
):
    site = make_site(org=operator.organisation, creator=operator)
    profile = make_site_profile(site=site, creator=operator)
    profile.inverter_continuous_kw = None
    db_session.flush()
    body = client.get(
        f"/sites/{site.site_id}/spare-capacity", headers=auth_headers(operator)
    ).json()
    assert body["hourly_inverter_headroom_kw"] is None


def test_site_without_profile_returns_404(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator)
    assert (
        client.get(
            f"/sites/{site.site_id}/spare-capacity", headers=auth_headers(operator)
        ).status_code
        == 404
    )


def test_field_agent_cannot_see_spare_capacity(
    client, field_agent, operator, auth_headers, make_site, make_site_profile
):
    site = make_site(org=operator.organisation, creator=operator)
    make_site_profile(site=site, creator=operator)
    assert (
        client.get(
            f"/sites/{site.site_id}/spare-capacity", headers=auth_headers(field_agent)
        ).status_code
        == 403
    )
