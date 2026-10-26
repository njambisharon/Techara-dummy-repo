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

def test_site_profile_can_be_created(db_session, make_site_profile):
    profile = make_site_profile()
    assert db_session.get(SiteProfile, profile.profile_id) is not None


def test_site_profile_version_must_be_positive(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(version=0),
    )


def test_site_profile_version_must_be_unique_per_site(db_session, make_site, make_site_profile):
    site = make_site()
    make_site_profile(site=site, version=1)
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(site=site, version=1),
    )


def test_site_profile_can_have_multiple_versions(db_session, make_site, make_site_profile):
    site = make_site()
    first = make_site_profile(site=site, version=1)
    second = make_site_profile(site=site, version=2)
    assert first.profile_id != second.profile_id


def test_site_profile_rejects_soc_min_not_below_soc_max(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(
            soc_min_percent=Decimal("90.00"),
            soc_max_percent=Decimal("80.00"),
        ),
    )


def test_site_profile_rejects_charge_efficiency_above_one(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(charge_efficiency=Decimal("1.100")),
    )


def test_site_profile_rejects_negative_tariff(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(tariff_per_kwh=Decimal("-1.00")),
    )


def test_site_profile_rejects_baseline_with_wrong_length(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(baseline_demand_kw=[1.0] * 23),
    )


def test_site_profile_rejects_missing_solar_profile_array(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(
            solar_profile={"average_kw": [5.0] * 24}
        ),
    )
