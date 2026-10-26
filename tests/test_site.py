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


def test_site_can_be_created_and_retrieved(db_session, make_site):
    site = make_site()
    assert db_session.get(Site, site.site_id).site_name == site.site_name


def test_duplicate_site_name_within_same_organisation_is_rejected(
    db_session, make_org, make_user, make_site
):
    org = make_org()
    creator = make_user(org=org)
    make_site(org=org, creator=creator, name="Same Site")
    assert_integrity_error(
        db_session,
        lambda: make_site(org=org, creator=creator, name="Same Site"),
    )


def test_same_site_name_is_allowed_for_different_organisations(
    db_session, make_org, make_user, make_site
):
    org1, org2 = make_org(), make_org()
    make_site(org=org1, creator=make_user(org=org1), name="Central")
    second = make_site(org=org2, creator=make_user(org=org2), name="Central")
    assert second.site_name == "Central"


def test_site_district_can_be_updated(db_session, make_site):
    site = make_site()
    site.district = "Lusaka"
    db_session.flush()
    db_session.refresh(site)
    assert site.district == "Lusaka"
