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


def test_reading_can_be_saved_and_retrieved(db_session, make_reading):
    reading = make_reading()
    db_session.flush()
    assert db_session.get(Reading, reading.reading_id) is not None


@pytest.mark.parametrize(
    "field,value",
    [
        ("current_a", Decimal("-0.001")),
        ("power_w", Decimal("-0.01")),
        ("energy_total_kwh", Decimal("-0.0001")),
        ("voltage_v", Decimal("301.00")),
    ],
)
def test_reading_rejects_invalid_measurements(db_session, make_reading, field, value):
    assert_integrity_error(
        db_session,
        lambda: make_reading(**{field: value}),
    )


def test_reading_rejects_duplicate_timestamp_for_same_assignment(db_session, make_assignment, make_reading):
    assignment = make_assignment()
    measured_at = datetime.now(timezone.utc)
    make_reading(assignment=assignment, measured_at=measured_at)
    assert_integrity_error(
        db_session,
        lambda: make_reading(assignment=assignment, measured_at=measured_at),
    )


def test_reading_allows_same_timestamp_for_different_assignments(db_session, make_assignment, make_reading):
    timestamp = datetime.now(timezone.utc)
    first = make_assignment()
    second = make_assignment()
    a = make_reading(assignment=first, measured_at=timestamp)
    b = make_reading(assignment=second, measured_at=timestamp)
    assert a.reading_id != b.reading_id


def test_reading_rejects_business_mismatch_for_assignment(db_session, make_assignment, make_business):
    assignment = make_assignment()
    other_business = make_business()
    assert_integrity_error(
        db_session,
        lambda: db_session.add(
            Reading(
                assignment_id=assignment.assignment_id,
                business_id=other_business.business_id,
                measured_at=datetime.now(timezone.utc),
                voltage_v=Decimal("230.00"),
                current_a=Decimal("1.000"),
                power_w=Decimal("230.00"),
                energy_total_kwh=Decimal("10.0000"),
            )
        ),
    )
