import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from repositories.reading_repository import reading_repository


class ReadingService:
    def get_latest(self, db: Session, assignment_id: uuid.UUID):
        reading = reading_repository.latest_for_assignment(db, assignment_id)
        if reading is None:
            raise HTTPException(status_code=404, detail="No readings for this install")
        return reading

    def list_recent(self, db: Session, assignment_id: uuid.UUID, limit: int):
        return reading_repository.recent_for_assignment(db, assignment_id, limit)


reading_service = ReadingService()
