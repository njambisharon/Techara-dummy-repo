from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from models.base import Base
from models.site_profile import SiteProfile


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


def test_site_profile_version_must_be_unique_per_site(
    db_session, make_site, make_site_profile
):
    site = make_site()
    make_site_profile(site=site, version=1)
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(site=site, version=1),
    )


def test_site_profile_can_have_multiple_versions(
    db_session, make_site, make_site_profile
):
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


def test_site_profile_rejects_charge_efficiency_above_one(
    db_session, make_site_profile
):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(charge_efficiency=Decimal("1.100")),
    )


def test_site_profile_rejects_negative_tariff(db_session, make_site_profile):
    assert_integrity_error(
        db_session,
        lambda: make_site_profile(tariff_per_kwh=Decimal("-1.00")),
    )
