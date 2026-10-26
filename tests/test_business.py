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



# Business tests

def test_business_can_be_created(db_session, make_business):
    business = make_business()
    assert db_session.get(Business, business.business_id) is not None


def test_business_default_connection_status_is_prospective(db_session, make_site, make_user):
    site = make_site()
    user = make_user()
    business = Business(
        site_id=site.site_id, logged_by=user.user_id,
        business_name=f"Default-{uuid4().hex[:8]}",
        business_type=BusinessType.MAIZE_MILL,
        owner_first_name="A", owner_last_name="B",
        operating_hours={"start": "08:00", "end": "17:00"},
        days_per_month=25,
    )
    db_session.add(business)
    db_session.flush()
    db_session.refresh(business)
    assert business.connection_status == ConnectionStatus.PROSPECTIVE


@pytest.mark.parametrize("days", [0, 32, -1])
def test_business_rejects_invalid_days_per_month(db_session, make_business, days):
    assert_integrity_error(
        db_session,
        lambda: make_business(days_per_month=days),
    )


def test_business_rejects_zero_startup_power(db_session, make_business):
    assert_integrity_error(
        db_session,
        lambda: make_business(
            startup_power_kw=Decimal("0.00"),
            startup_duration_s=10,
            startup_data_label=StartupDataLabel.ESTIMATED,
        ),
    )


def test_business_rejects_startup_power_without_data_label(db_session, make_business):
    assert_integrity_error(
        db_session,
        lambda: make_business(
            startup_power_kw=Decimal("2.00"),
            startup_duration_s=10,
            startup_data_label=None,
        ),
    )


def test_business_rejects_non_object_operating_hours(db_session, make_business):
    assert_integrity_error(
        db_session,
        lambda: make_business(operating_hours=["08:00", "17:00"]),
    )


def test_business_connection_status_can_be_updated(db_session, make_business):
    business = make_business()
    business.connection_status = ConnectionStatus.CONNECTED
    db_session.flush()
    db_session.refresh(business)
    assert business.connection_status == ConnectionStatus.CONNECTED
