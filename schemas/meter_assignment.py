import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class MeterAssignmentCreate(BaseModel):
    device_id: uuid.UUID
    business_id: uuid.UUID


class MeterAssignmentRemove(BaseModel):
    buffer_uploaded_confirmed: Literal[True]


class MeterAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment_id: uuid.UUID
    device_id: uuid.UUID
    business_id: uuid.UUID
    installed_at: datetime
    removed_at: datetime | None
    installed_by: uuid.UUID


class MeterAssignmentCreated(MeterAssignmentRead):
    device_token: str