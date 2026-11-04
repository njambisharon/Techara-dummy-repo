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

    def create(self, db: Session, assignment_id: uuid.UUID, data: dict) -> Reading:
        reading = Reading(assignment_id=assignment_id, **data)
        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading

    def get_by_measured_at(self, db, assignment_id, measured_at):
        return db.scalar(
            select(Reading).where(
                Reading.assignment_id == assignment_id,
                Reading.measured_at == measured_at,
            )
        )

    def get_for_assignment(self, db, assignment_id, reading_id):
        return db.scalar(
            select(Reading).where(
                Reading.assignment_id == assignment_id,
                Reading.reading_id == reading_id,
            )
        )

    def delete(self, db, reading: Reading) -> None:
        db.delete(reading)
        db.commit()


reading_repository = ReadingRepository()
