from models.meter_assignment import MeterAssignment
from models.sensor_device import SensorDevice
from sqlalchemy import select


class MeterAssignmentRepository:
    def create(self, db, assignment):
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def get_open_for_device(self, db, device_id):
        return db.scalar(
            select(MeterAssignment).where(
                MeterAssignment.device_id == device_id,
                MeterAssignment.removed_at.is_(None),
            )
        )

    def get_open_for_business(self, db, business_id):
        return db.scalar(
            select(MeterAssignment).where(
                MeterAssignment.business_id == business_id,
                MeterAssignment.removed_at.is_(None),
            )
        )

    def get_for_organisation(self, db, assignment_id, organisation_id):
        return db.scalar(
            select(MeterAssignment)
            .join(SensorDevice, MeterAssignment.device_id == SensorDevice.device_id)
            .where(
                MeterAssignment.assignment_id == assignment_id,
                SensorDevice.organisation_id == organisation_id,
            )
        )

    def save(self, db, assignment):
        db.commit()
        db.refresh(assignment)
        return assignment

    def list_for_device(self, db, device_id):
        return db.scalars(
            select(MeterAssignment)
            .where(MeterAssignment.device_id == device_id)
            .order_by(MeterAssignment.installed_at)
        ).all()

    def list_for_organisation(
        self, db, organisation_id, business_id=None, device_id=None, open_only=False
    ):
        query = (
            select(MeterAssignment)
            .join(SensorDevice, MeterAssignment.device_id == SensorDevice.device_id)
            .where(SensorDevice.organisation_id == organisation_id)
        )
        if business_id is not None:
            query = query.where(MeterAssignment.business_id == business_id)
        if device_id is not None:
            query = query.where(MeterAssignment.device_id == device_id)
        if open_only:
            query = query.where(MeterAssignment.removed_at.is_(None))
        return db.scalars(query.order_by(MeterAssignment.installed_at.desc())).all()


meter_assignment_repository = MeterAssignmentRepository()