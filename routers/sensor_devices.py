import uuid
from database import get_db
from fastapi import APIRouter, Depends, Query, status
from models.enums import DeviceStatus
from schemas.sensor_device import (
    SensorDeviceCreate,
    SensorDeviceRead,
    SensorDeviceStatusUpdate,
)
from services.sensor_device_service import sensor_device_service
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter(prefix="/devices", tags=["Sensor devices"])


@router.post(
    "",
    response_model=SensorDeviceRead,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    data: SensorDeviceCreate,
    db: Session = Depends(get_db),
):
    return sensor_device_service.register_device(db, data)


@router.get(
    "",
    response_model=list[SensorDeviceRead],
)
def list_devices(
    organisation_id: uuid.UUID,
    device_status: Optional[DeviceStatus] = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
):
    return sensor_device_service.list_devices(
        db,
        organisation_id,
        device_status,
    )


@router.patch(
    "/{device_id}/status",
    response_model=SensorDeviceRead,
)
def update_device_status(
    device_id: uuid.UUID,
    organisation_id: uuid.UUID,
    data: SensorDeviceStatusUpdate,
    db: Session = Depends(get_db),
):
    return sensor_device_service.update_status(
        db,
        device_id,
        data,
        organisation_id,
    )
