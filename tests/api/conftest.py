import os

os.environ.setdefault("JWT_SECRET", "test-only-signing-key-do-not-use-in-production")

import pytest
from core.security import create_access_token
from database import get_db
from fastapi.testclient import TestClient
from main import app
from models.enums import UserRole


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    def factory(user):
        token = create_access_token(user.user_id, user.role.value, user.organisation_id)
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def operator(make_user):
    return make_user(role=UserRole.OPERATOR)


@pytest.fixture
def field_agent(make_user, operator):
    return make_user(org=operator.organisation, role=UserRole.FIELD_AGENT)
