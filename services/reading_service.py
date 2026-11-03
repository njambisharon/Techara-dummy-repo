import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories.meter_assignment_repository import meter_assignment_repository
from repositories.reading_repository import reading_repository
from schemas.reading import ReadingCreate


class ReadingService:
    def get_latest(self, db: Session, assignment_id: uuid.UUID):
        reading = reading_repository.latest_for_assignment(db, assignment_id)
        if reading is None:
            raise HTTPException(status_code=404, detail="No readings for this install")
        return reading

    def list_recent(self, db: Session, assignment_id: uuid.UUID, limit: int):
        return reading_repository.recent_for_assignment(db, assignment_id, limit)

    def create(self, db: Session, assignment_id: uuid.UUID, payload: ReadingCreate):
        assignment = meter_assignment_repository.get(db, assignment_id)
        if assignment is None:
            raise HTTPException(status_code=404, detail="Assignment not found")

        now = datetime.now(timezone.utc)
        data = payload.model_dump(exclude_unset=True)
        if data.get("measured_at") is None:
            data["measured_at"] = now

        existing = reading_repository.get_by_measured_at(
            db, assignment_id, data["measured_at"]
        )
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="A reading already exists for this assignment at this time",
            )

        data["business_id"] = assignment.business_id

        return reading_repository.create(db, assignment_id, data)

    def delete(self, db: Session, assignment_id: uuid.UUID, reading_id: int) -> None:
        assignment = meter_assignment_repository.get(db, assignment_id)
        if assignment is None:
            raise HTTPException(status_code=404, detail="Assignment not found")

        reading = reading_repository.get_for_assignment(db, assignment_id, reading_id)
        if reading is None:
            raise HTTPException(status_code=404, detail="Reading not found")

        reading_repository.delete(db, reading)


reading_service = ReadingService()
