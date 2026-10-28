def test_latest_returns_highest_version(
    client, operator, auth_headers, make_site, make_site_profile
):
    site = make_site(org=operator.organisation, creator=operator)
    make_site_profile(site=site, creator=operator, version=1)
    newest = make_site_profile(site=site, creator=operator, version=2)
    response = client.get(
        f"/sites/{site.site_id}/profiles/latest", headers=auth_headers(operator)
    )
    assert response.status_code == 200
    assert response.json()["profile_id"] == str(newest.profile_id)


def test_latest_without_profiles_returns_404(client, operator, auth_headers, make_site):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.get(
        f"/sites/{site.site_id}/profiles/latest", headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_cannot_get_latest_for_other_organisation(
    client, operator, auth_headers, make_site_profile
):
    other_profile = make_site_profile()
    response = client.get(
        f"/sites/{other_profile.site_id}/profiles/latest",
        headers=auth_headers(operator),
    )
    assert response.status_code == 404


def test_field_agent_cannot_get_latest_profile(
    client, field_agent, operator, auth_headers, make_site_profile, make_site
):
    site = make_site(org=operator.organisation, creator=operator)
    make_site_profile(site=site, creator=operator)
    response = client.get(
        f"/sites/{site.site_id}/profiles/latest", headers=auth_headers(field_agent)
    )
    assert response.status_code == 403
