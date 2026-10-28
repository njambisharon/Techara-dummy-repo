import uuid
from datetime import datetime

from models.enums import DeviceStatus
from pydantic import BaseModel, ConfigDict, Field


class SensorDeviceCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    organisation_id: uuid.UUID
    registered_by: uuid.UUID
    device_serial: str = Field(min_length=1, max_length=50)


class SensorDeviceStatusUpdate(BaseModel):
    status: DeviceStatus


class SensorDeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: uuid.UUID
    organisation_id: uuid.UUID
    device_serial: str
    status: DeviceStatus
    registered_by: uuid.UUID
    created_at: datetime
