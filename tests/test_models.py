import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

import models
from models.base import Base


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
    assert len(models.__all__) == 10
    assert set(Base.metadata.tables) == expected


@pytest.mark.parametrize(
    "table_name",
    [
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
    ],
)
def test_every_table_has_a_primary_key(table_name):
    assert len(table(table_name).primary_key.columns) >= 1


@pytest.mark.parametrize(
    "table_name",
    [
        "users",
        "site",
        "site_profile",
        "business",
        "sensor_device",
        "meter_assignment",
        "reading",
        "scenario",
        "scenario_business",
    ],
)
def test_every_dependent_table_has_foreign_keys(table_name):
    assert len(table(table_name).foreign_key_constraints) >= 1
