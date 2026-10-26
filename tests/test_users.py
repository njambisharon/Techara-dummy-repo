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


def test_operator_user_can_be_created(db_session, make_org, make_user):
    user = make_user(org=make_org(), role=UserRole.OPERATOR)
    assert user.email
    assert user.phone_number is None


def test_field_agent_user_can_be_created(db_session, make_org, make_user):
    user = make_user(org=make_org(), role=UserRole.FIELD_AGENT)
    assert user.phone_number
    assert user.email is None


def test_operator_without_email_is_rejected(db_session, make_org):
    org = make_org()
    user = User(
        organisation_id=org.organisation_id, first_name="A", last_name="B",
        email=None, phone_number=None, password_hash="hash",
        role=UserRole.OPERATOR,
    )
    assert_integrity_error(db_session, lambda: db_session.add(user))


def test_field_agent_without_phone_is_rejected(db_session, make_org):
    org = make_org()
    user = User(
        organisation_id=org.organisation_id, first_name="A", last_name="B",
        email=None, phone_number=None, password_hash="hash",
        role=UserRole.FIELD_AGENT,
    )
    assert_integrity_error(db_session, lambda: db_session.add(user))


def test_duplicate_user_email_is_rejected(db_session, make_org, make_user):
    org = make_org()
    email = f"same-{uuid4().hex}@example.com"
    make_user(org=org, role=UserRole.OPERATOR, email=email)
    assert_integrity_error(
        db_session,
        lambda: make_user(org=org, role=UserRole.OPERATOR, email=email),
    )


def test_user_account_defaults_are_applied(db_session, make_org):
    org = make_org()
    user = User(
        organisation_id=org.organisation_id, first_name="A", last_name="B",
        email=f"default-{uuid4().hex}@example.com", password_hash="hash",
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    assert user.is_active is True
    assert user.must_change_password is False


def test_user_can_be_deactivated(db_session, make_user):
    user = make_user()
    user.is_active = False
    db_session.flush()
    db_session.refresh(user)
    assert user.is_active is False
