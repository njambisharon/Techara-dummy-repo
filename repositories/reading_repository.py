import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.reading import Reading


class ReadingRepository:
    def latest_for_assignment(
        self, db: Session, assignment_id: uuid.UUID
    ) -> Reading | None:
        return db.scalars(
            select(Reading)
            .where(Reading.assignment_id == assignment_id)
            .order_by(Reading.measured_at.desc())
            .limit(1)
        ).first()

    def recent_for_assignment(
        self, db: Session, assignment_id: uuid.UUID, limit: int = 50
    ) -> list[Reading]:
        return db.scalars(
            select(Reading)
            .where(Reading.assignment_id == assignment_id)
            .order_by(Reading.measured_at.desc())
            .limit(limit)
        ).all()


reading_repository = ReadingRepository()
