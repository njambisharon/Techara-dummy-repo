from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


if TYPE_CHECKING:
    from models.scenario import Scenario
    from models.site import Site


JSONType = JSON().with_variant(JSONB(), "postgresql")


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
    )

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("site.site_id"), nullable=False, index=True
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
    baseline_demand_kw: Mapped[list] = mapped_column(JSONType, nullable=False)
    solar_profile: Mapped[dict] = mapped_column(JSONType, nullable=False)
    settings: Mapped[dict] = mapped_column(JSONType, nullable=False)
    data_labels: Mapped[dict] = mapped_column(JSONType, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    site: Mapped["Site"] = relationship(back_populates="profiles")
    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="profile")
