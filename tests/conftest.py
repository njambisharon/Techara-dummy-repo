import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient

from database import get_db
from main import app

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from models.business import Business
from models.enums import (
    BusinessType,
    ConnectionStatus,
    DataLabel,
    DeviceStatus,
    LimitingCheck,
    Outcome,
    RevenueBasis,
    SolarDayType,
    UserRole,
)
from models.meter_assignment import MeterAssignment
from models.organisation import Organisation
from models.reading import Reading
from models.scenario import Scenario
from models.sensor_device import SensorDevice
from models.site import Site
from models.site_profile import SiteProfile
from models.user import User


@pytest.fixture(scope="session")
def engine():
    """
    Session-scoped SQLite engine for all tests.
    Works in CI without Docker or external Postgres.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_setup(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
        dbapi_conn.create_function("gen_random_uuid", 0, lambda: uuid.uuid4().hex)

    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def db_session(engine):
    """Transaction-scoped session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, expire_on_commit=False)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def operator(make_user):
    return make_user()


@pytest.fixture
def auth_headers():
    from core.security import create_access_token

    def factory(user):
        token = create_access_token(
            user_id=user.user_id,
            role=user.role.value,
            organisation_id=user.organisation_id,
        )
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def make_org(db_session):
    def factory(name=None):
        item = Organisation(organisation_name=name or f"Org-{uuid4().hex[:8]}")
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_user(db_session, make_org):
    def factory(
        org=None, role=UserRole.OPERATOR, email=None, phone=None, created_by=None
    ):
        org = org or make_org()
        suffix = uuid4().hex[:8]
        item = User(
            organisation_id=org.organisation_id,
            first_name="Test",
            last_name="User",
            email=email
            if email is not None
            else (f"user-{suffix}@example.com" if role == UserRole.OPERATOR else None),
            phone_number=phone
            if phone is not None
            else (
                f"+26097{uuid4().int % 10**7:07d}"
                if role == UserRole.FIELD_AGENT
                else None
            ),
            password_hash="test-password-hash",
            role=role,
            created_by=created_by.user_id if created_by else None,
        )
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_site(db_session, make_org, make_user):
    def factory(org=None, creator=None, name=None):
        org = org or make_org()
        creator = creator or make_user(org=org)
        item = Site(
            organisation_id=org.organisation_id,
            site_name=name or f"Site-{uuid4().hex[:8]}",
            district="Chongwe",
            created_by=creator.user_id,
        )
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_site_profile(db_session, make_site, make_user):
    def factory(site=None, creator=None, version=1, **overrides):
        site = site or make_site()
        creator = creator or make_user()
        values = dict(
            site_id=site.site_id,
            version=version,
            inverter_continuous_kw=Decimal("10.00"),
            inverter_surge_kw=Decimal("15.00"),
            inverter_surge_duration_s=10,
            battery_nominal_kwh=Decimal("40.00"),
            soc_min_percent=Decimal("20.00"),
            soc_max_percent=Decimal("90.00"),
            charge_efficiency=Decimal("0.950"),
            discharge_efficiency=Decimal("0.950"),
            max_charge_kw=Decimal("8.00"),
            max_discharge_kw=Decimal("8.00"),
            tariff_per_kwh=Decimal("2.50"),
            baseline_demand_kw=[0.5] * 24,
            solar_profile={
                "average_kw": [5.0] * 24,
                "low_sun_kw": [2.0] * 24,
            },
            settings={"min_observed_days": 7},
            data_labels={
                "baseline": "estimated",
                "solar": "estimated",
                "battery": "user_entered",
            },
            created_by=creator.user_id,
        )
        values.update(overrides)
        item = SiteProfile(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_business(db_session, make_site, make_user):
    def factory(site=None, logger=None, **overrides):
        site = site or make_site()
        logger = logger or make_user()
        values = dict(
            site_id=site.site_id,
            logged_by=logger.user_id,
            business_name=f"Business-{uuid4().hex[:8]}",
            business_type=BusinessType.MAIZE_MILL,
            owner_first_name="Amina",
            owner_last_name="Banda",
            owner_phone="+260977123456",
            connection_status=ConnectionStatus.PROSPECTIVE,
            operating_hours={"start": "08:00", "end": "17:00"},
            days_per_month=26,
        )
        values.update(overrides)
        item = Business(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_device(db_session, make_org, make_user):
    def factory(org=None, registrar=None, serial=None, **overrides):
        org = org or make_org()
        registrar = registrar or make_user(org=org)
        values = dict(
            organisation_id=org.organisation_id,
            device_serial=serial or f"DEV-{uuid4().hex[:10]}",
            status=DeviceStatus.ACTIVE,
            registered_by=registrar.user_id,
        )
        values.update(overrides)
        item = SensorDevice(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_assignment(db_session, make_device, make_business, make_user):
    def factory(device=None, business=None, installer=None, **overrides):
        device = device or make_device()
        business = business or make_business()
        installer = installer or make_user()
        values = dict(
            device_id=device.device_id,
            business_id=business.business_id,
            device_token_hash="test-token-hash",
            installed_at=datetime.now(timezone.utc) - timedelta(hours=1),
            removed_at=None,
            installed_by=installer.user_id,
        )
        values.update(overrides)
        item = MeterAssignment(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_reading(db_session, make_assignment):
    def factory(assignment=None, **overrides):
        assignment = assignment or make_assignment()
        values = dict(
            assignment_id=assignment.assignment_id,
            business_id=assignment.business_id,
            measured_at=datetime.now(timezone.utc),
            voltage_v=Decimal("230.00"),
            current_a=Decimal("2.000"),
            power_w=Decimal("460.00"),
            energy_total_kwh=Decimal("12.5000"),
        )
        values.update(overrides)
        item = Reading(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory


@pytest.fixture
def make_scenario(db_session, make_site_profile, make_user):
    def factory(profile=None, creator=None, **overrides):
        profile = profile or make_site_profile()
        creator = creator or make_user()
        values = dict(
            profile_id=profile.profile_id,
            name="Test scenario",
            initial_stored_kwh=Decimal("20.00"),
            solar_day_type=SolarDayType.LOW_SUN,
            period_days=7,
            outcome=Outcome.CONDITIONALLY_FEASIBLE,
            check_results={
                "power": True,
                "startup": True,
                "energy": False,
                "battery": True,
            },
            limiting_check=LimitingCheck.ENERGY,
            monthly_revenue=Decimal("125.00"),
            revenue_basis=RevenueBasis.PLANNED,
            lowest_stored_kwh=Decimal("5.00"),
            data_label=DataLabel.SIMULATED,
            metrics={"added_kwh": 50.0},
            simulation_trace={"hourly": [0.0] * 24},
            input_snapshot={"source": "test"},
            created_by=creator.user_id,
        )
        values.update(overrides)
        item = Scenario(**values)
        db_session.add(item)
        db_session.flush()
        return item

    return factory
