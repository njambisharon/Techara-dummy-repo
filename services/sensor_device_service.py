from fastapi import HTTPException

from models.sensor_device import SensorDevice
from repositories.sensor_device_repository import sensor_device_repository


class SensorDeviceService:
    def register_device(self, db, data):
        if sensor_device_repository.get_by_serial(db, data.device_serial):
            raise HTTPException(
                status_code=409,
                detail="A device with this serial is already registered",
            )

        device = SensorDevice(
            organisation_id=data.organisation_id,
            device_serial=data.device_serial,
            registered_by=data.registered_by,
        )

        return sensor_device_repository.create(db, device)

    def list_devices(self, db, organisation_id, device_status=None):
        return sensor_device_repository.list_for_organisation(
            db,
            organisation_id,
            device_status,
        )

    def get_device(self, db, device_id, organisation_id):
        device = sensor_device_repository.get_for_organisation(
            db,
            device_id,
            organisation_id,
        )

        if device is None:
            raise HTTPException(
                status_code=404,
                detail="Device not found",
            )

        return device

    def update_status(
        self,
        db,
        device_id,
        data,
        organisation_id,
    ):
        device = self.get_device(
            db,
            device_id,
            organisation_id,
        )

        device.status = data.status

        return sensor_device_repository.save(db, device)


sensor_device_service = SensorDeviceService()
