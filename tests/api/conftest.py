import os

os.environ.setdefault("JWT_SECRET", "test-only-signing-key-do-not-use-in-production")

import pytest

from datetime import datetime, timedelta
from decimal import Decimal

from core.defaults import SITE_TIMEZONE
from core.security import create_access_token
from database import get_db
from fastapi.testclient import TestClient
from main import app
from models.enums import UserRole

from models.enums import StartupDataLabel

SCENARIO_SETTINGS = {
    "reserve_factor": 0.2,
    "safety_margin": 0.1,
    "unserved_energy_tolerance_kwh": 0.5,
    "night_start_hour": 18,
    "night_end_hour": 6,
    "min_observed_days": 3,
}


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    def factory(user):
        token = create_access_token(user.user_id, user.role.value, user.organisation_id)
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture
def operator(make_user):
    return make_user(role=UserRole.OPERATOR)


@pytest.fixture
def field_agent(make_user, operator):
    return make_user(org=operator.organisation, role=UserRole.FIELD_AGENT)

@pytest.fixture
def make_scenario_site(db_session, make_site, make_site_profile, operator):
    def factory():
        site = make_site(org=operator.organisation, creator=operator)
        profile = make_site_profile(site=site, creator=operator)
        profile.settings = dict(SCENARIO_SETTINGS)
        db_session.flush()
        return profile

    return factory


@pytest.fixture
def scenario_site(make_scenario_site):
    return make_scenario_site()


@pytest.fixture
def metered_business(
    db_session, make_business, make_device, make_assignment, make_reading, operator
):
    def factory(site, kw="2000", days=3, open_hour=8, close_hour=17, **overrides):
        every_day = {
            day: {"open": open_hour, "close": close_hour}
            for day in (
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            )
        }
        values = {"operating_hours": every_day, "days_per_month": 26}
        values.update(overrides)
        business = make_business(site=site, logger=operator, **values)
        assignment = make_assignment(
            business=business, device=make_device(org=operator.organisation)
        )
        start = datetime.now(SITE_TIMEZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        hours = [
            hour % 24
            for hour in range(
                open_hour, close_hour if close_hour > open_hour else close_hour + 24
            )
        ]
        for day in range(1, days + 1):
            for hour in hours:
                reading = make_reading(
                    assignment=assignment,
                    measured_at=start - timedelta(days=day) + timedelta(hours=hour),
                )
                reading.power_w = Decimal(kw)
        db_session.flush()
        return business

    return factory


@pytest.fixture
def run_scenario(client, auth_headers, operator):
    def factory(profile, businesses, **overrides):
        payload = {
            "profile_id": str(profile.profile_id),
            "initial_stored_kwh": "20.00",
            "solar_day_type": "average",
            "period_days": 2,
            "business_ids": [str(business.business_id) for business in businesses],
        }
        payload.update(overrides)
        return client.post("/scenarios", json=payload, headers=auth_headers(operator))

    return factory


@pytest.fixture
def saved_scenario(run_scenario, scenario_site, metered_business):
    business = metered_business(
        scenario_site.site,
        startup_power_kw=Decimal("5.00"),
        startup_duration_s=3,
        startup_data_label=StartupDataLabel.USER_ENTERED,
    )
    return run_scenario(scenario_site, [business]).json()

