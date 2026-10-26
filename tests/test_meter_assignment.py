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

def test_meter_assignment_can_be_created(db_session, make_assignment):
    assignment = make_assignment()
    assert db_session.get(MeterAssignment, assignment.assignment_id) is not None


def test_device_cannot_have_two_open_assignments(db_session, make_assignment, make_device, make_business):
    device = make_device()
    make_assignment(device=device, business=make_business())
    assert_integrity_error(
        db_session,
        lambda: make_assignment(device=device, business=make_business()),
    )


def test_business_cannot_have_two_open_assignments(db_session, make_assignment, make_business, make_device):
    business = make_business()
    make_assignment(business=business, device=make_device())
    assert_integrity_error(
        db_session,
        lambda: make_assignment(business=business, device=make_device()),
    )


def test_closed_assignment_allows_sensor_reassignment(db_session, make_assignment, make_device, make_business):
    device = make_device()
    first_business = make_business()
    first = make_assignment(device=device, business=first_business)
    first.removed_at = datetime.now(timezone.utc)
    db_session.flush()
    second = make_assignment(device=device, business=make_business())
    assert second.assignment_id != first.assignment_id


def test_assignment_rejects_removal_before_installation(db_session, make_assignment):
    installed = datetime.now(timezone.utc)
    assert_integrity_error(
        db_session,
        lambda: make_assignment(
            installed_at=installed,
            removed_at=installed - timedelta(minutes=1),
        ),
    )


def test_assignment_keeps_historical_record_after_removal(db_session, make_assignment):
    assignment = make_assignment()
    assignment.removed_at = datetime.now(timezone.utc)
    db_session.flush()
    assert db_session.get(MeterAssignment, assignment.assignment_id).removed_at is not None
