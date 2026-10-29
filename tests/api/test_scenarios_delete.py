import uuid
from datetime import datetime, timezone

from models.enums import Decision
from models.scenario_business import ScenarioBusiness
from sqlalchemy import select


def test_delete_scenario(client, operator, auth_headers, saved_scenario):
    url = f"/scenarios/{saved_scenario['scenario_id']}"
    assert client.delete(url, headers=auth_headers(operator)).status_code == 204
    assert client.get(url, headers=auth_headers(operator)).status_code == 404


def test_deleted_scenario_leaves_the_list(
    client, operator, auth_headers, saved_scenario
):
    client.delete(
        f"/scenarios/{saved_scenario['scenario_id']}", headers=auth_headers(operator)
    )
    assert client.get("/scenarios", headers=auth_headers(operator)).json() == []


def test_scenario_with_a_decision_cannot_be_deleted(
    client, db_session, operator, auth_headers, saved_scenario
):
    link = db_session.scalars(
        select(ScenarioBusiness).where(
            ScenarioBusiness.scenario_id == uuid.UUID(saved_scenario["scenario_id"])
        )
    ).first()
    link.decision = next(iter(Decision))
    link.decided_by = operator.user_id
    link.decided_at = datetime.now(timezone.utc)
    db_session.flush()
    response = client.delete(
        f"/scenarios/{saved_scenario['scenario_id']}", headers=auth_headers(operator)
    )
    assert response.status_code == 409


def test_delete_unknown_scenario_returns_404(client, operator, auth_headers):
    response = client.delete(
        f"/scenarios/{uuid.uuid4()}", headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_delete_other_organisation_scenario_returns_404(
    client, operator, auth_headers, make_scenario
):
    other = make_scenario()
    response = client.delete(
        f"/scenarios/{other.scenario_id}", headers=auth_headers(operator)
    )
    assert response.status_code == 404


def test_field_agent_cannot_delete(client, field_agent, auth_headers):
    response = client.delete(
        f"/scenarios/{uuid.uuid4()}", headers=auth_headers(field_agent)
    )
    assert response.status_code == 403
