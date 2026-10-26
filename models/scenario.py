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
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import (
    DataLabel,
    LimitingCheck,
    Outcome,
    RevenueBasis,
    SolarDayType,
    varchar_enum,
)


if TYPE_CHECKING:
    from models.scenario_business import ScenarioBusiness
    from models.site_profile import SiteProfile


# Portable JSON type: JSONB on Postgres, JSON on SQLite
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Scenario(Base):
    __tablename__ = "scenario"
    __table_args__ = (
        CheckConstraint("initial_stored_kwh >= 0", name="ck_scenario_initial_stored"),
        CheckConstraint("period_days >= 1", name="ck_scenario_period_days"),
    )

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("site_profile.profile_id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(100))
    initial_stored_kwh: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    solar_day_type: Mapped[SolarDayType] = mapped_column(
        varchar_enum(SolarDayType, 10, "ck_scenario_solar_day_type"),
        nullable=False,
        server_default=SolarDayType.LOW_SUN.value,
    )
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[Outcome] = mapped_column(
        varchar_enum(Outcome, 25, "ck_scenario_outcome"), nullable=False
    )
    check_results: Mapped[dict] = mapped_column(JSONType, nullable=False)
    limiting_check: Mapped[LimitingCheck | None] = mapped_column(
        varchar_enum(LimitingCheck, 10, "ck_scenario_limiting_check")
    )
    monthly_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    revenue_basis: Mapped[RevenueBasis | None] = mapped_column(
        varchar_enum(RevenueBasis, 10, "ck_scenario_revenue_basis")
    )
    lowest_stored_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    data_label: Mapped[DataLabel] = mapped_column(
        varchar_enum(DataLabel, 15, "ck_scenario_data_label"), nullable=False
    )
    metrics: Mapped[dict] = mapped_column(JSONType, nullable=False)
    simulation_trace: Mapped[dict] = mapped_column(JSONType, nullable=False)
    input_snapshot: Mapped[dict] = mapped_column(JSONType, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    profile: Mapped["SiteProfile"] = relationship(back_populates="scenarios")
    business_links: Mapped[list["ScenarioBusiness"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", passive_deletes=True
    )
