import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token
from database import get_db
from main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def set_test_jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET", "test-only-secret-for-auth-tests-longer-than-32-bytes"
    )

def test_get_current_user_profile(db_session, make_user):
    user = make_user()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_access_token(
    user_id=user.user_id,
    role=user.role.value,
    organisation_id=user.organisation_id,
    )
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(user.user_id)
        assert data["first_name"] == user.first_name
        assert data["last_name"] == user.last_name
        assert data["role"] == user.role.value
        assert "password_hash" not in data
    finally:
        app.dependency_overrides.clear()


def test_get_current_user_profile_requires_authentication():
    response = client.get("/users/me")

    assert response.status_code == 401

def test_update_current_user_profile(db_session, make_user):
    user = make_user()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_access_token(
            user_id=user.user_id,
            role=user.role.value,
            organisation_id=user.organisation_id,
        )

        response = client.patch(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"first_name": "Emma", "last_name": "Updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Emma"
        assert data["last_name"] == "Updated"

        db_session.refresh(user)
        assert user.first_name == "Emma"
        assert user.last_name == "Updated"
    finally:
        app.dependency_overrides.clear()


def test_update_profile_rejects_duplicate_email(db_session, make_user):
    user = make_user()
    other_user = make_user()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_access_token(
            user_id=user.user_id,
            role=user.role.value,
            organisation_id=user.organisation_id,
        )

        response = client.patch(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": other_user.email},
        )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_update_profile_rejects_duplicate_phone(db_session, make_user):
    from models.enums import UserRole

    user = make_user()
    other_user = make_user(role=UserRole.FIELD_AGENT)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_access_token(
            user_id=user.user_id,
            role=user.role.value,
            organisation_id=user.organisation_id,
        )

        response = client.patch(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone_number": other_user.phone_number},
        )

        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_update_profile_rejects_empty_request(db_session, make_user):
    user = make_user()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        token = create_access_token(
            user_id=user.user_id,
            role=user.role.value,
            organisation_id=user.organisation_id,
        )

        response = client.patch(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
