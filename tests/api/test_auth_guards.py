import pytest
from core.roles import OPERATOR_ONLY
from core.security import create_access_token
from database import get_db
from dependencies import get_current_user, require_roles
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def guarded_client(db_session):
    guarded_app = FastAPI()

    @guarded_app.get("/me")
    def me(user=Depends(get_current_user)):
        return {"user_id": str(user.user_id)}

    @guarded_app.get("/operators-only")
    def operators_only(user=Depends(require_roles(*OPERATOR_ONLY))):
        return {"ok": True}

    def override_get_db():
        yield db_session

    guarded_app.dependency_overrides[get_db] = override_get_db
    return TestClient(guarded_app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_token_is_rejected(guarded_client):
    assert guarded_client.get("/me").status_code == 401


def test_garbage_token_is_rejected(guarded_client):
    response = guarded_client.get(
        "/me", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401


def test_expired_token_is_rejected(guarded_client, operator):
    token = create_access_token(
        operator.user_id,
        operator.role.value,
        operator.organisation_id,
        expires_minutes=-1,
    )
    response = guarded_client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_returns_user(guarded_client, operator, auth_headers):
    response = guarded_client.get("/me", headers=auth_headers(operator))
    assert response.status_code == 200
    assert response.json()["user_id"] == str(operator.user_id)


def test_deactivated_user_is_rejected(
    guarded_client, db_session, operator, auth_headers
):
    operator.is_active = False
    db_session.flush()
    assert guarded_client.get("/me", headers=auth_headers(operator)).status_code == 401


def test_field_agent_blocked_from_operator_route(
    guarded_client, field_agent, auth_headers
):
    response = guarded_client.get("/operators-only", headers=auth_headers(field_agent))
    assert response.status_code == 403


def test_operator_allowed_on_operator_route(guarded_client, operator, auth_headers):
    response = guarded_client.get("/operators-only", headers=auth_headers(operator))
    assert response.status_code == 200
