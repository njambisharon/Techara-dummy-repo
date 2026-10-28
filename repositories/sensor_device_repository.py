from models.enums import DeviceStatus
from models.meter_assignment import MeterAssignment
from models.sensor_device import SensorDevice
from sqlalchemy import select

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


class SensorDeviceRepository:
    def create(self, db, device):
        db.add(device)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Invalid organisation_id or registered_by",
            )
        db.refresh(device)
        return device
    def get_by_serial(self, db, device_serial):
        return db.scalar(
            select(SensorDevice).where(SensorDevice.device_serial == device_serial)
        )

    def list_for_organisation(self, db, organisation_id, device_status=None):
        query = select(SensorDevice).where(
            SensorDevice.organisation_id == organisation_id
        )
        if device_status is not None:
            query = query.where(SensorDevice.status == device_status)
        return db.scalars(query.order_by(SensorDevice.device_serial)).all()

    def get_for_organisation(self, db, device_id, organisation_id):
        return db.scalar(
            select(SensorDevice).where(
                SensorDevice.device_id == device_id,
                SensorDevice.organisation_id == organisation_id,
            )
        )

    def has_open_assignment(self, db, device_id):
        return (
            db.scalar(
                select(MeterAssignment.assignment_id).where(
                    MeterAssignment.device_id == device_id,
                    MeterAssignment.removed_at.is_(None),
                )
            )
            is not None
        )

    def list_installable(self, db, organisation_id):
        open_install = (
            select(MeterAssignment.assignment_id)
            .where(
                MeterAssignment.device_id == SensorDevice.device_id,
                MeterAssignment.removed_at.is_(None),
            )
            .exists()
        )
        return db.scalars(
            select(SensorDevice)
            .where(
                SensorDevice.organisation_id == organisation_id,
                SensorDevice.status == DeviceStatus.ACTIVE,
                ~open_install,
            )
            .order_by(SensorDevice.device_serial)
        ).all()

    def save(self, db, device):
        db.commit()
        db.refresh(device)
        return device


sensor_device_repository = SensorDeviceRepository()