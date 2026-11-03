import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ReadingCreate(BaseModel):
    measured_at: datetime | None = None
    voltage_v: Decimal
    current_a: Decimal
    power_w: Decimal
    energy_total_kwh: Decimal = Field(ge=0)


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reading_id: int
    assignment_id: uuid.UUID
    business_id: uuid.UUID
    measured_at: datetime
    received_at: datetime
    voltage_v: Decimal
    current_a: Decimal
    power_w: Decimal
    energy_total_kwh: Decimal

    @field_serializer("voltage_v", "current_a", "power_w", "energy_total_kwh")
    def to_number(self, value: Decimal) -> float:
        return float(value)
