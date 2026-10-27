from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from models.base import Base
from models.enums import (
    DeviceStatus,
)
from models.sensor_device import SensorDevice


def table(name):
    return Base.metadata.tables[name]


def assert_integrity_error(session, operation):
    with pytest.raises(IntegrityError):
        operation()
        session.flush()
    session.rollback()


def test_sensor_device_can_be_registered(db_session, make_device):
    device = make_device()
    assert db_session.get(SensorDevice, device.device_id) is not None


def test_sensor_device_serial_must_be_unique(db_session, make_device):
    serial = f"SERIAL-{uuid4().hex}"
    make_device(serial=serial)
    assert_integrity_error(
        db_session,
        lambda: make_device(serial=serial),
    )


def test_sensor_device_default_model_and_status(db_session, make_org, make_user):
    org = make_org()
    device = SensorDevice(
        organisation_id=org.organisation_id,
        device_serial=f"DEV-{uuid4().hex}",
        registered_by=make_user(org=org).user_id,
    )
    db_session.add(device)
    db_session.flush()
    db_session.refresh(device)
    assert device.model == "PZEM-004T"
    assert device.status == DeviceStatus.ACTIVE


def test_sensor_device_status_can_be_changed(db_session, make_device):
    device = make_device()
    device.status = DeviceStatus.FAULTY
    db_session.flush()
    db_session.refresh(device)
    assert device.status == DeviceStatus.FAULTY
