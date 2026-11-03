import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from core.dependencies import get_current_user
from database import get_db
from models.enums import DeviceStatus
from repositories.meter_assignment_repository import meter_assignment_repository as REPO
from routers.meter_assignments import router

app = FastAPI()
app.include_router(router)

AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture
def fake_user():
    return SimpleNamespace(
        user_id=uuid.uuid4(),
        organisation_id=uuid.uuid4(),
        role="field_agent",
        is_active=True,
        must_change_password=False,
    )


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db, fake_user):
    def override_get_db():
        yield mock_db

    def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def device_id():
    return str(uuid.uuid4())


@pytest.fixture
def business_id():
    return str(uuid.uuid4())


@pytest.fixture
def assignment_id():
    return str(uuid.uuid4())


def make_device(device_id, org_id, status=DeviceStatus.ACTIVE):
    return SimpleNamespace(device_id=device_id, organisation_id=org_id, status=status)


def make_business(business_id):
    return SimpleNamespace(business_id=business_id, site_id=uuid.uuid4())


def make_assignment(assignment_id, installed_by, removed_at=None):
    return SimpleNamespace(
        assignment_id=assignment_id,
        device_id=uuid.uuid4(),
        business_id=uuid.uuid4(),
        installed_at=datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc),
        removed_at=removed_at,
        installed_by=installed_by,
    )


def patch_install_lookups(
    monkeypatch,
    device=None,
    business=None,
    open_device=None,
    open_business=None,
):
    monkeypatch.setattr(
        REPO,
        "get_device_for_organisation",
        lambda db, device_id, organisation_id: device,
    )
    monkeypatch.setattr(
        REPO,
        "get_business_for_organisation",
        lambda db, business_id, organisation_id: business,
    )
    monkeypatch.setattr(REPO, "get_open_for_device", lambda db, device_id: open_device)
    monkeypatch.setattr(
        REPO, "get_open_for_business", lambda db, business_id: open_business
    )


def test_install_meter_success(
    client, mock_db, device_id, business_id, fake_user, monkeypatch
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id),
        business=make_business(business_id),
    )

    def fill_on_refresh(obj):
        obj.assignment_id = uuid.uuid4()
        obj.installed_at = datetime.now(timezone.utc)
        obj.removed_at = None

    mock_db.refresh.side_effect = fill_on_refresh

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )

    assert response.status_code == 201
    body = response.json()
    assert "assignment_id" in body
    assert "device_token" in body


def test_install_device_not_found(client, device_id, business_id, monkeypatch):
    patch_install_lookups(monkeypatch, device=None, business=make_business(business_id))

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 404


def test_install_business_not_found(
    client, device_id, business_id, fake_user, monkeypatch
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id),
        business=None,
    )

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 404


@pytest.mark.parametrize("status", [DeviceStatus.FAULTY, DeviceStatus.RETIRED])
def test_install_inactive_device_conflicts(
    client, device_id, business_id, fake_user, monkeypatch, status
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id, status=status),
        business=make_business(business_id),
    )

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 409


def test_install_device_already_installed_conflicts(
    client, device_id, business_id, fake_user, monkeypatch
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id),
        business=make_business(business_id),
        open_device=make_assignment(uuid.uuid4(), fake_user.user_id),
    )

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 409


def test_install_business_already_has_meter_conflicts(
    client, device_id, business_id, fake_user, monkeypatch
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id),
        business=make_business(business_id),
        open_business=make_assignment(uuid.uuid4(), fake_user.user_id),
    )

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 409


def test_install_integrity_error_rolls_back(
    client, mock_db, device_id, business_id, fake_user, monkeypatch
):
    patch_install_lookups(
        monkeypatch,
        device=make_device(device_id, fake_user.organisation_id),
        business=make_business(business_id),
    )

    def raise_integrity(db, assignment):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    monkeypatch.setattr(REPO, "create", raise_integrity)

    response = client.post(
        "/assignments",
        json={"device_id": device_id, "business_id": business_id},
        headers=AUTH,
    )
    assert response.status_code == 409
    mock_db.rollback.assert_called_once()


def test_install_missing_device_id(client, business_id):
    response = client.post(
        "/assignments", json={"business_id": business_id}, headers=AUTH
    )
    assert response.status_code == 422


def test_install_missing_business_id(client, device_id):
    response = client.post("/assignments", json={"device_id": device_id}, headers=AUTH)
    assert response.status_code == 422


def test_install_invalid_uuid(client):
    response = client.post(
        "/assignments",
        json={"device_id": "not-a-uuid", "business_id": "also-not-a-uuid"},
        headers=AUTH,
    )
    assert response.status_code == 422


def _record_list(monkeypatch):
    calls = []

    def fake_list(
        db, organisation_id, business_id=None, device_id=None, open_only=False
    ):
        calls.append(
            {"business_id": business_id, "device_id": device_id, "open_only": open_only}
        )
        return []

    monkeypatch.setattr(REPO, "list_for_organisation", fake_list)
    return calls


def test_list_assignments(client, monkeypatch):
    calls = _record_list(monkeypatch)

    response = client.get("/assignments", headers=AUTH)

    assert response.status_code == 200
    assert response.json() == []
    assert len(calls) == 1


def test_list_with_business_filter(client, monkeypatch, business_id):
    calls = _record_list(monkeypatch)

    response = client.get(f"/assignments?business_id={business_id}", headers=AUTH)

    assert response.status_code == 200
    assert calls[0]["business_id"] is not None


def test_list_with_device_filter(client, monkeypatch, device_id):
    calls = _record_list(monkeypatch)

    response = client.get(f"/assignments?device_id={device_id}", headers=AUTH)

    assert response.status_code == 200
    assert calls[0]["device_id"] is not None


def test_list_open_only(client, monkeypatch):
    calls = _record_list(monkeypatch)

    response = client.get("/assignments?open_only=true", headers=AUTH)

    assert response.status_code == 200
    assert calls[0]["open_only"] is True


def test_remove_meter_success(client, assignment_id, fake_user, monkeypatch):
    assignment = make_assignment(assignment_id, fake_user.user_id)
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: assignment)
    monkeypatch.setattr(REPO, "save", lambda db, a: a)

    response = client.post(
        f"/assignments/{assignment_id}/remove",
        json={"buffer_uploaded_confirmed": True},
        headers=AUTH,
    )

    assert response.status_code == 200
    assert assignment.removed_at is not None


def test_remove_meter_not_found(client, assignment_id, monkeypatch):
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: None)

    response = client.post(
        f"/assignments/{assignment_id}/remove",
        json={"buffer_uploaded_confirmed": True},
        headers=AUTH,
    )
    assert response.status_code == 404


def test_remove_meter_already_removed_conflicts(
    client, assignment_id, fake_user, monkeypatch
):
    assignment = make_assignment(
        assignment_id,
        fake_user.user_id,
        removed_at=datetime(2026, 10, 29, 9, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: assignment)

    response = client.post(
        f"/assignments/{assignment_id}/remove",
        json={"buffer_uploaded_confirmed": True},
        headers=AUTH,
    )
    assert response.status_code == 409


def test_remove_buffer_not_confirmed_is_rejected(
    client, assignment_id, fake_user, monkeypatch
):
    assignment = make_assignment(assignment_id, fake_user.user_id)
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: assignment)

    response = client.post(
        f"/assignments/{assignment_id}/remove",
        json={"buffer_uploaded_confirmed": False},
        headers=AUTH,
    )
    assert response.status_code == 422
    assert assignment.removed_at is None


def test_remove_missing_confirmation(client, assignment_id):
    response = client.post(
        f"/assignments/{assignment_id}/remove", json={}, headers=AUTH
    )
    assert response.status_code == 422


def test_remove_invalid_assignment_id(client):
    response = client.post(
        "/assignments/not-a-uuid/remove",
        json={"buffer_uploaded_confirmed": True},
        headers=AUTH,
    )
    assert response.status_code == 422


def test_get_meter_assignment_success(client, assignment_id, fake_user, monkeypatch):
    assignment = make_assignment(assignment_id, fake_user.user_id)
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: assignment)

    response = client.get(f"/assignments/{assignment_id}", headers=AUTH)

    assert response.status_code == 200
    assert response.json()["assignment_id"] == assignment_id


def test_get_meter_assignment_not_found(client, monkeypatch):
    monkeypatch.setattr(REPO, "get_for_organisation", lambda db, aid, org: None)

    response = client.get(
        "/assignments/00000000-0000-0000-0000-000000000000", headers=AUTH
    )
    assert response.status_code == 404


def test_repo_create_adds_and_commits(mock_db):
    obj = MagicMock()
    REPO.create(mock_db, obj)
    mock_db.add.assert_called_once_with(obj)
    mock_db.commit.assert_called()
    mock_db.refresh.assert_called_with(obj)


def test_repo_save_commits_and_refreshes(mock_db):
    obj = MagicMock()
    REPO.save(mock_db, obj)
    mock_db.commit.assert_called()
    mock_db.refresh.assert_called_with(obj)


def test_repo_get_device_for_organisation(mock_db):
    REPO.get_device_for_organisation(mock_db, uuid.uuid4(), uuid.uuid4())
    mock_db.scalar.assert_called_once()


def test_repo_get_open_for_device(mock_db):
    REPO.get_open_for_device(mock_db, uuid.uuid4())
    mock_db.scalar.assert_called_once()


def test_repo_get_open_for_business(mock_db):
    REPO.get_open_for_business(mock_db, uuid.uuid4())
    mock_db.scalar.assert_called_once()


def test_repo_get_for_organisation(mock_db):
    REPO.get_for_organisation(mock_db, uuid.uuid4(), uuid.uuid4())
    mock_db.scalar.assert_called_once()


def test_repo_list_for_organisation_all_filters(mock_db):
    REPO.list_for_organisation(
        mock_db,
        uuid.uuid4(),
        business_id=uuid.uuid4(),
        device_id=uuid.uuid4(),
        open_only=True,
    )
    mock_db.scalars.assert_called_once()


def test_repo_list_for_organisation_no_filters(mock_db):
    REPO.list_for_organisation(mock_db, uuid.uuid4())
    mock_db.scalars.assert_called_once()


def test_get_business_for_organisation_returns_none_for_other_org(
    db_session, make_org, make_site, make_business
):
    org_a = make_org()
    org_b = make_org()
    site = make_site(org=org_a)
    business = make_business(site=site)

    result = REPO.get_business_for_organisation(
        db_session, business.business_id, org_b.organisation_id
    )
    assert result is None


def test_get_business_for_organisation_finds_own_org(
    db_session, make_org, make_site, make_business
):
    org = make_org()
    site = make_site(org=org)
    business = make_business(site=site)

    result = REPO.get_business_for_organisation(
        db_session, business.business_id, org.organisation_id
    )
    assert result is not None
