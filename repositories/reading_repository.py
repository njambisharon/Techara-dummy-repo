from models.reading import Reading
from sqlalchemy import select


class ReadingRepository:
    def latest_for_assignment(self, db, assignment_id):
        return db.scalar(
            select(Reading)
            .where(Reading.assignment_id == assignment_id)
            .order_by(Reading.measured_at.desc(), Reading.reading_id.desc())
        )

    def recent_for_assignment(self, db, assignment_id, limit: int):
        return db.scalars(
            select(Reading)
            .where(Reading.assignment_id == assignment_id)
            .order_by(Reading.measured_at.desc(), Reading.reading_id.desc())
            .limit(limit)
        ).all()

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

    def create(self, db, assignment_id, data):
        reading = Reading(assignment_id=assignment_id, **data)
        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading

    def delete(self, db, reading):
        db.delete(reading)
        db.commit()


reading_repository = ReadingRepository()
