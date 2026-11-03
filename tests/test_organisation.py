from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models.base import Base
from models.organisation import Organisation
from models.site import Site


def table(name):
    return Base.metadata.tables[name]


def assert_integrity_error(session, operation):
    with pytest.raises(IntegrityError):
        operation()
        session.flush()
    session.rollback()


def test_organisation_can_be_created_and_retrieved(db_session, make_org):
    org = make_org()
    fetched = db_session.get(Organisation, org.organisation_id)
    assert fetched is not None
    assert fetched.organisation_name == org.organisation_name


def test_organisation_name_must_not_be_null(db_session):
    assert_integrity_error(
        db_session,
        lambda: db_session.add(Organisation(organisation_name=None)),
    )


def test_organisation_name_must_be_unique(db_session, make_org):
    name = f"Duplicate-{uuid4().hex}"
    make_org(name=name)
    assert_integrity_error(
        db_session,
        lambda: db_session.add(Organisation(organisation_name=name)),
    )


def test_organisation_can_have_multiple_sites(
    db_session, make_org, make_user, make_site
):
    org = make_org()
    user = make_user(org=org)
    make_site(org=org, creator=user, name="Site A")
    make_site(org=org, creator=user, name="Site B")
    saved_sites = db_session.scalars(
        select(Site).where(Site.organisation_id == org.organisation_id)
    ).all()
    assert len(saved_sites) == 2
