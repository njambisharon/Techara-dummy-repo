import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from models.enums import BusinessType, ConnectionStatus, StartupDataLabel


class BusinessCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    site_id: uuid.UUID
    business_name: str = Field(min_length=1, max_length=100)
    business_type: BusinessType
    owner_first_name: str = Field(min_length=1, max_length=100)
    owner_last_name: str = Field(min_length=1, max_length=100)
    owner_phone: str | None = Field(default=None, max_length=20)
    operating_hours: dict
    days_per_month: int = Field(ge=1, le=31)


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: uuid.UUID
    site_id: uuid.UUID
    logged_by: uuid.UUID
    business_name: str
    business_type: BusinessType
    owner_first_name: str
    owner_last_name: str
    owner_phone: str | None
    connection_status: ConnectionStatus
    operating_hours: dict
    days_per_month: int
    startup_power_kw: Decimal | None
    startup_duration_s: int | None
    startup_data_label: StartupDataLabel | None
    created_at: datetime


class BusinessUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    business_name: str | None = Field(default=None, min_length=1, max_length=100)
    business_type: BusinessType | None = None
    owner_first_name: str | None = Field(default=None, min_length=1, max_length=100)
    owner_last_name: str | None = Field(default=None, min_length=1, max_length=100)
    owner_phone: str | None = Field(default=None, max_length=20)
    operating_hours: dict | None = None
    days_per_month: int | None = Field(default=None, ge=1, le=31)


class HourlyBusinessProfilePoint(BaseModel):
    hour: int = Field(ge=0, le=23)
    average_power_kw: float | None
    reading_count: int = Field(ge=0)


class BusinessProfileRead(BaseModel):
    business_id: uuid.UUID
    hours: list[HourlyBusinessProfilePoint]
