from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from models.base import Base
from models.scenario import Scenario


def table(name):
    return Base.metadata.tables[name]


def assert_integrity_error(session, operation):
    with pytest.raises(IntegrityError):
        operation()
        session.flush()
    session.rollback()


def test_scenario_can_be_created(db_session, make_scenario):
    scenario = make_scenario()
    assert db_session.get(Scenario, scenario.scenario_id) is not None


def test_scenario_rejects_negative_initial_stored_energy(db_session, make_scenario):
    assert_integrity_error(
        db_session,
        lambda: make_scenario(initial_stored_kwh=Decimal("-1.00")),
    )


def test_scenario_rejects_zero_period_days(db_session, make_scenario):
    assert_integrity_error(
        db_session,
        lambda: make_scenario(period_days=0),
    )


def test_scenario_rejects_missing_check_result_keys(db_session, make_scenario):
    assert_integrity_error(
        db_session,
        lambda: make_scenario(check_results={"power": True}),
    )


def test_scenario_metrics_can_be_updated(db_session, make_scenario):
    scenario = make_scenario()
    scenario.metrics = {"added_kwh": 75.0, "monthly_revenue": 187.5}
    db_session.flush()
    db_session.refresh(scenario)
    assert scenario.metrics["added_kwh"] == 75.0
