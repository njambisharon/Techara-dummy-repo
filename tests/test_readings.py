import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_db
from main import app
from models.reading import Reading
from repositories.reading_repository import reading_repository
from services.reading_service import reading_service

SEEDED_ASSIGNMENT = "4c082973-3119-4af2-86c1-2ec87b8418f8"
UNKNOWN_ASSIGNMENT = "00000000-0000-0000-0000-000000000000"
DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
needs_db = pytest.mark.skipif(
    not DB_URL, reason="set TEST_DATABASE_URL to run database tests"
)

client = TestClient(app)


def fake_reading(reading_id=1):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        reading_id=reading_id,
        assignment_id=uuid.UUID(SEEDED_ASSIGNMENT),
        business_id=uuid.UUID("c5cd6d2a-c2d5-4b2b-b798-2a7fa6146bd3"),
        measured_at=now,
        received_at=now,
        voltage_v=Decimal("230.5"),
        current_a=Decimal("5.2"),
        power_w=Decimal("1198.6"),
        energy_total_kwh=Decimal("100.25"),
    )


@pytest.fixture
def mock_repo():
    with patch("services.reading_service.reading_repository") as repo:
        yield repo


class TestReadingService:
    def test_get_latest_returns_reading_when_found(self, mock_repo):
        reading = object()
        mock_repo.latest_for_assignment.return_value = reading

        result = reading_service.get_latest(
            db=MagicMock(), assignment_id=uuid.UUID(SEEDED_ASSIGNMENT)
        )

        assert result is reading

    def test_get_latest_raises_404_when_missing(self, mock_repo):
        mock_repo.latest_for_assignment.return_value = None

        with pytest.raises(HTTPException) as exc:
            reading_service.get_latest(
                db=MagicMock(), assignment_id=uuid.UUID(SEEDED_ASSIGNMENT)
            )

        assert exc.value.status_code == 404
        assert exc.value.detail == "No readings for this install"

    def test_list_recent_passes_limit_to_repository(self, mock_repo):
        db = object()
        mock_repo.recent_for_assignment.return_value = []

        result = reading_service.list_recent(
            db=db, assignment_id=uuid.UUID(SEEDED_ASSIGNMENT), limit=10
        )

        assert result == []
        mock_repo.recent_for_assignment.assert_called_once_with(
            db, uuid.UUID(SEEDED_ASSIGNMENT), 10
        )


class TestReadingsApi:
    @pytest.fixture(autouse=True)
    def override_db(self):
        app.dependency_overrides[get_db] = lambda: None
        yield
        app.dependency_overrides.clear()

    def test_latest_reading_returns_200(self):
        with patch.object(reading_service, "get_latest", return_value=fake_reading()):
            response = client.get(f"/assignments/{SEEDED_ASSIGNMENT}/latest-reading")

        assert response.status_code == 200
        body = response.json()
        assert body["reading_id"] == 1
        assert body["voltage_v"] == 230.5

    def test_latest_reading_returns_404_when_missing(self):
        error = HTTPException(status_code=404, detail="No readings for this install")
        with patch.object(reading_service, "get_latest", side_effect=error):
            response = client.get(f"/assignments/{SEEDED_ASSIGNMENT}/latest-reading")

        assert response.status_code == 404
        assert response.json()["detail"] == "No readings for this install"

    def test_recent_readings_returns_list(self):
        readings = [fake_reading(1), fake_reading(2)]
        with patch.object(reading_service, "list_recent", return_value=readings):
            response = client.get(f"/assignments/{SEEDED_ASSIGNMENT}/readings?limit=2")

        assert response.status_code == 200
        assert [r["reading_id"] for r in response.json()] == [1, 2]

    def test_recent_readings_defaults_limit_to_50(self):
        with patch.object(reading_service, "list_recent", return_value=[]) as mock_list:
            client.get(f"/assignments/{SEEDED_ASSIGNMENT}/readings")

        assert mock_list.call_args.args[2] == 50

    @pytest.mark.parametrize("limit", [0, 201])
    def test_recent_readings_rejects_out_of_range_limit(self, limit):
        with patch.object(reading_service, "list_recent", return_value=[]) as mock_list:
            response = client.get(
                f"/assignments/{SEEDED_ASSIGNMENT}/readings?limit={limit}"
            )

        assert response.status_code == 422
        mock_list.assert_not_called()

    def test_invalid_uuid_returns_422(self):
        response = client.get("/assignments/not-a-uuid/latest-reading")

        assert response.status_code == 422


class TestReadingsDatabase:
    @pytest.fixture
    def db(self):
        engine = create_engine(DB_URL)
        session = sessionmaker(bind=engine)()
        yield session
        session.close()
        engine.dispose()

    @pytest.fixture
    def seeded_id(self):
        return uuid.UUID(os.getenv("TEST_ASSIGNMENT_ID", SEEDED_ASSIGNMENT))

    def test_seeded_assignment_has_readings(self, db, seeded_id):
        count = db.query(Reading).filter(Reading.assignment_id == seeded_id).count()
        assert count > 0

    def test_latest_matches_first_of_recent(self, db, seeded_id):
        latest = reading_repository.latest_for_assignment(db, seeded_id)
        recent = reading_repository.recent_for_assignment(db, seeded_id, 50)

        assert latest.reading_id == recent[0].reading_id

    def test_recent_is_ordered_newest_first(self, db, seeded_id):
        recent = reading_repository.recent_for_assignment(db, seeded_id, 50)

        times = [r.measured_at for r in recent]
        assert times == sorted(times, reverse=True)

    def test_unknown_assignment_has_no_latest(self, db):
        assert reading_repository.latest_for_assignment(db, uuid.uuid4()) is None
