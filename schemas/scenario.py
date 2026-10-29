import uuid
from datetime import datetime
from decimal import Decimal

from models.enums import (
    DataLabel,
    Decision,
    LimitingCheck,
    Outcome,
    RevenueBasis,
    SolarDayType,
)
from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    profile_id: uuid.UUID
    name: str | None = Field(default=None, max_length=100)
    initial_stored_kwh: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    solar_day_type: SolarDayType = SolarDayType.LOW_SUN
    period_days: int = Field(default=1, ge=1, le=31)
    business_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class CompareSitesCreate(BaseModel):
    site_ids: list[uuid.UUID] = Field(min_length=2, max_length=5)
    business_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)
    name: str | None = Field(default=None, max_length=100)
    initial_soc_percent: Decimal | None = Field(
        default=None, ge=0, le=100, max_digits=5, decimal_places=2
    )
    solar_day_type: SolarDayType = SolarDayType.LOW_SUN
    period_days: int = Field(default=1, ge=1, le=31)


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)


class ScenarioBusinessRead(BaseModel):
    business_id: uuid.UUID
    business_name: str
    decision: Decision | None
    decision_note: str | None
    decided_by: uuid.UUID | None
    decided_at: datetime | None


class ScenarioSummary(BaseModel):
    scenario_id: uuid.UUID
    profile_id: uuid.UUID
    profile_version: int
    site_id: uuid.UUID
    site_name: str
    name: str | None
    solar_day_type: SolarDayType
    period_days: int
    outcome: Outcome
    limiting_check: LimitingCheck | None
    monthly_revenue: Decimal | None
    revenue_basis: RevenueBasis | None
    lowest_stored_kwh: Decimal
    data_label: DataLabel
    created_by: uuid.UUID
    created_at: datetime
    rank: int | None = None
    businesses: list[ScenarioBusinessRead]


class ScenarioRead(ScenarioSummary):
    initial_stored_kwh: Decimal
    check_results: dict
    metrics: dict
    simulation_trace: dict
    input_snapshot: dict
