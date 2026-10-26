from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, UniqueConstraint, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

import models
from models.base import Base
from models.enums import (
    BusinessType, ConnectionStatus, DataLabel, Decision, DeviceStatus,
    LimitingCheck, Outcome, RevenueBasis, SolarDayType, StartupDataLabel,
    UserRole,
)
from models.organisation import Organisation
from models.user import User
from models.site import Site
from models.site_profile import SiteProfile
from models.business import Business
from models.sensor_device import SensorDevice
from models.meter_assignment import MeterAssignment
from models.reading import Reading
from models.scenario import Scenario
from models.scenario_business import ScenarioBusiness


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
