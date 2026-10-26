from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


if TYPE_CHECKING:
    from models.scenario import Scenario
    from models.site import Site


class SiteProfile(Base):
    __tablename__ = "site_profile"
    __table_args__ = (
        UniqueConstraint("site_id", "version", name="uq_site_profile_site_version"),
        CheckConstraint("version >= 1", name="ck_site_profile_version"),
        CheckConstraint(
            "inverter_continuous_kw > 0", name="ck_site_profile_inverter_continuous"
        ),
        CheckConstraint("inverter_surge_kw > 0", name="ck_site_profile_inverter_surge"),
        CheckConstraint(
            "inverter_surge_duration_s > 0",
            name="ck_site_profile_inverter_surge_duration",
        ),
        CheckConstraint(
            "battery_nominal_kwh > 0", name="ck_site_profile_battery_nominal"
        ),
        CheckConstraint(
            "soc_min_percent BETWEEN 0 AND 100", name="ck_site_profile_soc_min_range"
        ),
        CheckConstraint(
            "soc_max_percent BETWEEN 0 AND 100", name="ck_site_profile_soc_max_range"
        ),
        CheckConstraint(
            "soc_min_percent < soc_max_percent", name="ck_site_profile_soc_order"
        ),
        CheckConstraint(
            "charge_efficiency > 0 AND charge_efficiency <= 1",
            name="ck_site_profile_charge_efficiency",
        ),
        CheckConstraint(
            "discharge_efficiency > 0 AND discharge_efficiency <= 1",
            name="ck_site_profile_discharge_efficiency",
        ),
        CheckConstraint("max_charge_kw > 0", name="ck_site_profile_max_charge"),
        CheckConstraint("max_discharge_kw > 0", name="ck_site_profile_max_discharge"),
        CheckConstraint("tariff_per_kwh >= 0", name="ck_site_profile_tariff"),
        CheckConstraint(
            "jsonb_typeof(baseline_demand_kw) = 'array' AND jsonb_array_length(baseline_demand_kw) = 24",
            name="ck_site_profile_baseline_shape",
        ),
        CheckConstraint(
            "solar_profile ? 'average_kw' AND solar_profile ? 'low_sun_kw' AND "
            "jsonb_typeof(solar_profile -> 'average_kw') = 'array' "
            "AND jsonb_array_length(solar_profile -> 'average_kw') = 24 "
            "AND jsonb_typeof(solar_profile -> 'low_sun_kw') = 'array' "
            "AND jsonb_array_length(solar_profile -> 'low_sun_kw') = 24",
            name="ck_site_profile_solar_shape",
        ),
        CheckConstraint(
            "settings ? 'min_observed_days'", name="ck_site_profile_settings_shape"
        ),
        CheckConstraint(
            "data_labels ?& array['baseline', 'solar', 'battery']",
            name="ck_site_profile_data_labels_shape",
        ),
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.site_id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    inverter_continuous_kw: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    inverter_surge_kw: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    inverter_surge_duration_s: Mapped[int | None] = mapped_column(Integer)
    battery_nominal_kwh: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    soc_min_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    soc_max_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    charge_efficiency: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    discharge_efficiency: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    max_charge_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    max_discharge_kw: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    tariff_per_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    baseline_demand_kw: Mapped[list] = mapped_column(JSONB, nullable=False)
    solar_profile: Mapped[dict] = mapped_column(JSONB, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    data_labels: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    site: Mapped["Site"] = relationship(back_populates="profiles")
    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="profile")
