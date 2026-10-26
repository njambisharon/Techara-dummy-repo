from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from models.base import Base
from models.enums import (
    Decision,
)
from models.scenario_business import ScenarioBusiness


def table(name):
    return Base.metadata.tables[name]


def assert_integrity_error(session, operation):
    with pytest.raises(IntegrityError):
        operation()
        session.flush()
    session.rollback()


def test_scenario_can_link_a_business(db_session, make_scenario, make_business):
    scenario = make_scenario()
    business = make_business()
    link = ScenarioBusiness(
        scenario_id=scenario.scenario_id,
        business_id=business.business_id,
    )
    db_session.add(link)
    db_session.flush()
    assert (
        db_session.get(ScenarioBusiness, (scenario.scenario_id, business.business_id))
        is not None
    )


def test_scenario_business_rejects_duplicate_link(
    db_session, make_scenario, make_business
):
    scenario = make_scenario()
    business = make_business()
    db_session.add(
        ScenarioBusiness(
            scenario_id=scenario.scenario_id,
            business_id=business.business_id,
        )
    )
    db_session.flush()
    assert_integrity_error(
        db_session,
        lambda: db_session.add(
            ScenarioBusiness(
                scenario_id=scenario.scenario_id,
                business_id=business.business_id,
            )
        ),
    )


def test_scenario_business_rejects_incomplete_decision(
    db_session, make_scenario, make_business
):
    scenario = make_scenario()
    business = make_business()
    link = ScenarioBusiness(
        scenario_id=scenario.scenario_id,
        business_id=business.business_id,
        decision=Decision.PURSUE,
        decided_by=None,
        decided_at=None,
    )
    assert_integrity_error(db_session, lambda: db_session.add(link))


def test_scenario_business_accepts_complete_decision(
    db_session, make_scenario, make_business, make_user
):
    scenario = make_scenario()
    business = make_business()
    user = make_user()
    link = ScenarioBusiness(
        scenario_id=scenario.scenario_id,
        business_id=business.business_id,
        decision=Decision.PURSUE,
        decision_note="Suitable after site review",
        decided_by=user.user_id,
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add(link)
    db_session.flush()
    assert link.decision == Decision.PURSUE


def test_deleting_scenario_cascades_to_scenario_business_links(
    db_session, make_scenario, make_business
):
    scenario = make_scenario()
    business = make_business()
    link = ScenarioBusiness(
        scenario_id=scenario.scenario_id,
        business_id=business.business_id,
    )
    db_session.add(link)
    db_session.flush()
    scenario_id = scenario.scenario_id
    business_id = business.business_id

    db_session.delete(scenario)
    db_session.flush()

    db_session.expire_all()
    assert db_session.get(ScenarioBusiness, (scenario_id, business_id)) is None
