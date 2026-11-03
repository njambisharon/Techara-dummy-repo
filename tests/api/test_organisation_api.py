from repositories.organisation_repository import organisation_repository


def test_get_current_organisation(client, operator, auth_headers):
    response = client.get(
        "/organisation",
        headers=auth_headers(operator),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["organisation_id"] == str(operator.organisation_id)
    assert data["organisation_name"] == operator.organisation.organisation_name
    assert "created_at" in data


def test_get_organisation_requires_authentication(client):
    response = client.get("/organisation")

    assert response.status_code == 401


def test_get_organisation_requires_password_change(
    client, operator, auth_headers, db_session
):
    operator.must_change_password = True
    db_session.flush()

    response = client.get(
        "/organisation",
        headers=auth_headers(operator),
    )

    assert response.status_code == 403


def test_get_organisation_not_found(client, operator, auth_headers, monkeypatch):
    monkeypatch.setattr(
        organisation_repository,
        "get_by_id",
        lambda db, organisation_id: None,
    )

    response = client.get(
        "/organisation",
        headers=auth_headers(operator),
    )

    assert response.status_code == 404
