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

def test_all_ten_models_register_and_relationships_configure():
    configure_mappers()
    expected = {
        "organisation", "users", "site", "site_profile", "business",
        "sensor_device", "meter_assignment", "reading", "scenario",
        "scenario_business",
    }
    assert len(models.__all__) == 10
    assert set(Base.metadata.tables) == expected


@pytest.mark.parametrize("table_name", [
    "organisation", "users", "site", "site_profile", "business",
    "sensor_device", "meter_assignment", "reading", "scenario",
    "scenario_business",
])
def test_every_table_has_a_primary_key(table_name):
    assert len(table(table_name).primary_key.columns) >= 1


@pytest.mark.parametrize("table_name", [
    "users", "site", "site_profile", "business", "sensor_device",
    "meter_assignment", "reading", "scenario", "scenario_business",
])
def test_every_dependent_table_has_foreign_keys(table_name):
    assert len(table(table_name).foreign_key_constraints) >= 1
