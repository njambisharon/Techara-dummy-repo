import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from database import get_db
from main import app
from models.organisation import Organisation
from models.user import User
from services.auth_service import password_hasher

client = TestClient(app)


@pytest.fixture(autouse=True)
def set_test_jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET", "test-only-secret-for-auth-tests-longer-than-32-bytes"
    )


def test_signup_creates_operator(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.post(
            "/auth/signup",
            json={
                "first_name": "Emma",
                "last_name": "Mwelwa",
                "email": "emma.signup@example.com",
                "organisation_name": "Signup Test Org",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        assert "message" in response.json()

        user = db_session.scalar(
            select(User).where(User.email == "emma.signup@example.com")
        )
        assert user is not None
        assert user.role.value == "operator"
        assert password_hasher.verify("SecurePass123!", user.password_hash)
        assert (
            db_session.scalar(
                select(Organisation).where(
                    Organisation.organisation_id == user.organisation_id
                )
            )
            is not None
        )
    finally:
        app.dependency_overrides.clear()


def test_signup_duplicate_email_does_not_create_another_account(db_session):
    from models.enums import UserRole

    org = Organisation(organisation_name="Existing Email Org")
    db_session.add(org)
    db_session.flush()

    user = User(
        organisation_id=org.organisation_id,
        first_name="Existing",
        last_name="User",
        email="existing.signup@example.com",
        password_hash="existing-hash",
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    db_session.commit()

    before_users = db_session.scalar(select(func.count()).select_from(User))
    before_orgs = db_session.scalar(select(func.count()).select_from(Organisation))

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.post(
            "/auth/signup",
            json={
                "first_name": "Another",
                "last_name": "Person",
                "email": "existing.signup@example.com",
                "organisation_name": "Should Not Be Created",
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 201
        assert db_session.scalar(select(func.count()).select_from(User)) == before_users
        assert (
            db_session.scalar(select(func.count()).select_from(Organisation))
            == before_orgs
        )
    finally:
        app.dependency_overrides.clear()


def test_signup_rejects_duplicate_organisation_name(db_session):
    db_session.add(Organisation(organisation_name="Already Exists"))
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.post(
            "/auth/signup",
            json={
                "first_name": "New",
                "last_name": "Operator",
                "email": "new.operator@example.com",
                "organisation_name": "Already Exists",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_signup_rejects_short_password():
    response = client.post(
        "/auth/signup",
        json={
            "first_name": "New",
            "last_name": "Operator",
            "email": "short.password@example.com",
            "organisation_name": "Short Password Org",
            "password": "123",
        },
    )
    assert response.status_code == 422


def create_auth_test_user(db_session, phone_number=None):
    from models.enums import UserRole

    org = Organisation(organisation_name="Auth Test Organisation")
    db_session.add(org)
    db_session.flush()

    user = User(
        organisation_id=org.organisation_id,
        first_name="Auth",
        last_name="Tester",
        email=f"auth-{phone_number or 'email'}@example.com",
        phone_number=phone_number,
        password_hash=password_hasher.hash("CurrentPass123!"),
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_login_with_email_returns_access_token(db_session):
    create_auth_test_user(db_session)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "CurrentPass123!",
            },
        )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]
    finally:
        app.dependency_overrides.clear()


def test_login_rejects_incorrect_password(db_session):
    create_auth_test_user(db_session)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "WrongPass123!",
            },
        )

        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_login_with_phone_number_returns_access_token(db_session):
    phone_number = "+260977123456"
    create_auth_test_user(db_session, phone_number=phone_number)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.post(
            "/auth/login",
            json={
                "identifier": phone_number,
                "password": "CurrentPass123!",
            },
        )

        assert response.status_code == 200
        assert response.json()["access_token"]
    finally:
        app.dependency_overrides.clear()


def test_change_password_with_correct_current_password(db_session):
    create_auth_test_user(db_session)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        login_response = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "CurrentPass123!",
            },
        )
        assert login_response.status_code == 200

        token = login_response.json()["access_token"]
        response = client.patch(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "CurrentPass123!",
                "new_password": "NewSecurePass456!",
            },
        )

        assert response.status_code == 200
        assert password_hasher.verify(
            "NewSecurePass456!",
            db_session.query(User)
            .filter_by(email="auth-email@example.com")
            .one()
            .password_hash,
        )

        new_login = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "NewSecurePass456!",
            },
        )
        assert new_login.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_change_password_rejects_incorrect_current_password(db_session):
    create_auth_test_user(db_session)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        login_response = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "CurrentPass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = client.patch(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPass123!",
                "new_password": "NewSecurePass456!",
            },
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_change_password_rejects_reusing_current_password(db_session):
    create_auth_test_user(db_session)

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        login_response = client.post(
            "/auth/login",
            json={
                "identifier": "auth-email@example.com",
                "password": "CurrentPass123!",
            },
        )
        token = login_response.json()["access_token"]

        response = client.patch(
            "/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "CurrentPass123!",
                "new_password": "CurrentPass123!",
            },
        )

        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_change_password_requires_authentication():
    response = client.patch(
        "/auth/change-password",
        json={
            "current_password": "CurrentPass123!",
            "new_password": "NewSecurePass456!",
        },
    )

    assert response.status_code in (401, 403)
