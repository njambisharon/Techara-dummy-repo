def test_profiles_are_listed_newest_first(
    client, operator, auth_headers, make_site, make_site_profile
):
    site = make_site(org=operator.organisation, creator=operator)
    make_site_profile(site=site, creator=operator, version=1)
    make_site_profile(site=site, creator=operator, version=2)
    response = client.get(
        f"/sites/{site.site_id}/profiles", headers=auth_headers(operator)
    )
    assert response.status_code == 200
    assert [profile["version"] for profile in response.json()] == [2, 1]


def test_site_without_profiles_returns_empty_list(
    client, operator, auth_headers, make_site
):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.get(
        f"/sites/{site.site_id}/profiles", headers=auth_headers(operator)
    )
    assert response.json() == []


def test_field_agent_cannot_list_profiles(
    client, field_agent, operator, auth_headers, make_site
):
    site = make_site(org=operator.organisation, creator=operator)
    response = client.get(
        f"/sites/{site.site_id}/profiles", headers=auth_headers(field_agent)
    )
    assert response.status_code == 403


def test_cannot_list_other_organisation_profiles(
    client, operator, auth_headers, make_site_profile
):
    other_profile = make_site_profile()
    response = client.get(
        f"/sites/{other_profile.site_id}/profiles", headers=auth_headers(operator)
    )
    assert response.status_code == 404
