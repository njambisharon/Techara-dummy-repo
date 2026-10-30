import pytest

from core.database_url import normalize_database_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "postgres://user:password@localhost:5432/gridfit",
            "postgresql://user:password@localhost:5432/gridfit",
        ),
        (
            "postgresql://user:password@localhost:5432/gridfit",
            "postgresql://user:password@localhost:5432/gridfit",
        ),
        (
            "sqlite:///./test.db",
            "sqlite:///./test.db",
        ),
        (None, None),
        ("", ""),
    ],
)
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected
