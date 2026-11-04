import uuid

import pytest
from fastapi.testclient import TestClient

from database import get_db
from main import app


@pytest.fixture
def device_payload(operator):
    return {
        "organisation_id": str(operator.organisation_id),
        "registered_by": str(operator.user_id),
        "device_serial": f"PZEM-{uuid.uuid4().hex[:8]}",
    }


def register(client, payload):
    return client.post("/devices", json=payload)


def test_register_device_returns_201(client, device_payload):
    response = register(client, device_payload)

    assert response.status_code == 201
    body = response.json()
    assert body["device_serial"] == device_payload["device_serial"]
    assert body["status"] == "active"


def test_register_duplicate_serial_returns_409(client, device_payload):
    register(client, device_payload)

    response = register(client, device_payload)

    assert response.status_code == 409


def test_register_ignores_body_organisation(client, device_payload, operator):
    device_payload["organisation_id"] = str(uuid.uuid4())

    response = register(client, device_payload)

    assert response.status_code == 201
    assert response.json()["organisation_id"] == str(operator.organisation_id)


def test_register_missing_field_returns_422(client, device_payload):
    del device_payload["device_serial"]

    response = register(client, device_payload)

    assert response.status_code == 422


def test_list_devices_includes_registered_device(client, device_payload, operator):
    register(client, device_payload)

    response = client.get(
        "/devices", params={"organisation_id": str(operator.organisation_id)}
    )

    assert response.status_code == 200
    serials = [d["device_serial"] for d in response.json()]
    assert device_payload["device_serial"] in serials


@pytest.mark.parametrize("new_status", ["active", "faulty", "retired"])
def test_update_status_returns_200(client, device_payload, operator, new_status):
    device_id = register(client, device_payload).json()["device_id"]

    response = client.patch(
        f"/devices/{device_id}/status",
        params={"organisation_id": str(operator.organisation_id)},
        json={"status": new_status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == new_status


def test_update_status_rejects_invalid_value(client, device_payload, operator):
    device_id = register(client, device_payload).json()["device_id"]

    response = client.patch(
        f"/devices/{device_id}/status",
        params={"organisation_id": str(operator.organisation_id)},
        json={"status": "inactive"},
    )

    assert response.status_code == 422


def test_update_status_unknown_device_returns_404(client, operator):
    response = client.patch(
        f"/devices/{uuid.uuid4()}/status",
        params={"organisation_id": str(operator.organisation_id)},
        json={"status": "faulty"},
    )

    assert response.status_code == 404


def test_list_devices_filters_by_status(client, device_payload, operator):
    device_id = register(client, device_payload).json()["device_id"]
    client.patch(
        f"/devices/{device_id}/status",
        params={"organisation_id": str(operator.organisation_id)},
        json={"status": "faulty"},
    )

    response = client.get(
        "/devices",
        params={"organisation_id": str(operator.organisation_id), "status": "active"},
    )

    assert response.status_code == 200
    assert device_id not in [d["device_id"] for d in response.json()]


def test_list_devices_filters_by_faulty_status(client, device_payload, operator):
    device_id = register(client, device_payload).json()["device_id"]
    client.patch(
        f"/devices/{device_id}/status",
        params={"organisation_id": str(operator.organisation_id)},
        json={"status": "faulty"},
    )

    response = client.get(
        "/devices",
        params={"organisation_id": str(operator.organisation_id), "status": "faulty"},
    )

    assert device_id in [d["device_id"] for d in response.json()]


def test_list_devices_is_scoped_to_organisation(client, device_payload, operator):
    register(client, device_payload)

    response = client.get("/devices", params={"organisation_id": str(uuid.uuid4())})

    assert response.status_code == 200
    assert response.json() == []


def test_register_stores_device_with_default_status(client, device_payload):
    response = register(client, device_payload)

    assert response.json()["status"] == "active"
