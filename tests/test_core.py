from core.defaults import SITE_TIMEZONE, SUGGESTED_SETTINGS
from core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    InvalidDataError,
    NotFoundError,
)


def test_error_status_codes():
    assert AppError.status_code == 400
    assert NotFoundError.status_code == 404
    assert ConflictError.status_code == 409
    assert ForbiddenError.status_code == 403
    assert InvalidDataError.status_code == 422


def test_errors_keep_their_detail():
    error = NotFoundError("Site not found")
    assert error.detail == "Site not found"


def test_errors_are_app_errors():
    for error_class in (NotFoundError, ConflictError, ForbiddenError, InvalidDataError):
        assert issubclass(error_class, AppError)


def test_site_timezone_is_lusaka():
    assert SITE_TIMEZONE.key == "Africa/Lusaka"


def test_suggested_settings_has_min_observed_days():
    assert SUGGESTED_SETTINGS["min_observed_days"] == 3
