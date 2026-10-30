import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from models.enums import DataLabel
from pydantic import BaseModel, ConfigDict, Field, model_validator


Hourly = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class SolarProfile(BaseModel):
    average_kw: list[Hourly] = Field(min_length=24, max_length=24)
    low_sun_kw: list[Hourly] = Field(min_length=24, max_length=24)


class ProfileSettings(BaseModel):
    reserve_factor: float = Field(ge=0, le=1)
    safety_margin: float = Field(ge=0, le=0.5)
    unserved_energy_tolerance_kwh: float = Field(ge=0)
    night_start_hour: int = Field(ge=0, le=23)
    night_end_hour: int = Field(ge=0, le=23)
    min_observed_days: int = Field(ge=1, le=60)


class DataLabels(BaseModel):
    baseline: DataLabel
    solar: DataLabel
    battery: DataLabel


class SiteProfileCreate(BaseModel):
    inverter_continuous_kw: Decimal | None = Field(
        default=None, gt=0, max_digits=8, decimal_places=2
    )
    inverter_surge_kw: Decimal | None = Field(
        default=None, gt=0, max_digits=8, decimal_places=2
    )
    inverter_surge_duration_s: int | None = Field(default=None, gt=0)
    battery_nominal_kwh: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    soc_min_percent: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    soc_max_percent: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    charge_efficiency: Decimal = Field(gt=0, le=1, max_digits=4, decimal_places=3)
    discharge_efficiency: Decimal = Field(gt=0, le=1, max_digits=4, decimal_places=3)
    max_charge_kw: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    max_discharge_kw: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    tariff_per_kwh: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    baseline_demand_kw: list[Hourly] = Field(min_length=24, max_length=24)
    solar_profile: SolarProfile
    settings: ProfileSettings
    data_labels: DataLabels

    @model_validator(mode="after")
    def check_limits(self):
        if self.soc_min_percent >= self.soc_max_percent:
            raise ValueError("soc_min_percent must be lower than soc_max_percent")
        if (
            self.inverter_surge_kw is not None
            and self.inverter_continuous_kw is not None
            and self.inverter_surge_kw < self.inverter_continuous_kw
        ):
            raise ValueError(
                "inverter_surge_kw cannot be lower than inverter_continuous_kw"
            )
        return self


class SiteProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: uuid.UUID
    site_id: uuid.UUID
    version: int
    inverter_continuous_kw: Decimal | None
    inverter_surge_kw: Decimal | None
    inverter_surge_duration_s: int | None
    battery_nominal_kwh: Decimal
    soc_min_percent: Decimal
    soc_max_percent: Decimal
    charge_efficiency: Decimal
    discharge_efficiency: Decimal
    max_charge_kw: Decimal
    max_discharge_kw: Decimal
    tariff_per_kwh: Decimal
    baseline_demand_kw: list[float]
    solar_profile: dict
    settings: dict
    data_labels: dict
    created_by: uuid.UUID
    created_at: datetime


class ColumnMap(BaseModel):
    timestamp: str = Field(min_length=1)
    load_kw: str = Field(min_length=1)
    solar_kw: str = Field(min_length=1)


class MonitoringImport(BaseModel):
    csv_text: str = Field(min_length=1, max_length=10_000_000)
    source_timezone: str = "Africa/Lusaka"
    column_map: ColumnMap | None = None


class MonitoringImportRead(BaseModel):
    baseline_demand_kw: list[float]
    solar_profile: dict
    suggested_settings: dict
    suggested_data_labels: dict
    days_in_export: int
    complete_days: int
    low_sun_date: date
    first_date: date
    last_date: date
    rows_read: int
    rows_skipped: int


class SpareCapacityRead(BaseModel):
    site_id: uuid.UUID
    profile_id: uuid.UUID
    profile_version: int
    hourly_inverter_headroom_kw: list[float] | None
    usable_battery_kwh: float
    min_stored_kwh: float
    max_stored_kwh: float
    days: dict
