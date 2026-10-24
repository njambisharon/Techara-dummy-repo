from sqlalchemy.orm import configure_mappers

import models
from models.base import Base

EXPECTED_TABLES = {
    "organisation",
    "users",
    "site",
    "site_profile",
    "business",
    "sensor_device",
    "meter_assignment",
    "reading",
    "scenario",
    "scenario_business",
}


def test_all_models_load_and_register_their_tables():
    configure_mappers()
    assert len(models.__all__) == 10
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_a_meter_and_a_business_can_only_have_one_open_install():
    indexes = {index.name: index for index in Base.metadata.tables["meter_assignment"].indexes}
    for name in ("uq_meter_assignment_open_device", "uq_meter_assignment_open_business"):
        assert indexes[name].unique
        assert str(indexes[name].dialect_options["postgresql"]["where"]) == "removed_at IS NULL"


def test_a_reading_must_match_its_install_business():
    composite = [
        fk
        for fk in Base.metadata.tables["reading"].foreign_key_constraints
        if fk.name == "fk_reading_assignment_business"
    ]
    assert len(composite) == 1
    assert [column.name for column in composite[0].columns] == ["assignment_id", "business_id"]


def test_operators_need_an_email_and_field_agents_need_a_phone():
    checks = {c.name: str(c.sqltext) for c in Base.metadata.tables["users"].constraints if c.name}
    assert "ck_users_login_identifier" in checks
    assert "phone_number IS NOT NULL" in checks["ck_users_login_identifier"]
    assert "email IS NOT NULL" in checks["ck_users_login_identifier"]