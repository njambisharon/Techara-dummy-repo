from fastapi.testclient import TestClient
from sqlalchemy import func, select

from database import get_db
from main import app
from models.organisation import Organisation
from models.user import User
from services.auth_service import password_hasher

client = TestClient(app)


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
        assert db_session.scalar(
            select(Organisation).where(
                Organisation.organisation_id == user.organisation_id
            )
        ) is not None
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
    before_orgs = db_session.scalar(
        select(func.count()).select_from(Organisation)
    )

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
        assert db_session.scalar(
            select(func.count()).select_from(User)
        ) == before_users
        assert db_session.scalar(
            select(func.count()).select_from(Organisation)
        ) == before_orgs
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
