from sqlalchemy import (
    CheckConstraint,
    Column,
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
from sqlalchemy.orm import relationship

from models.base import Base
from models.enums import (
    DataLabel,
    LimitingCheck,
    Outcome,
    RevenueBasis,
    SolarDayType,
    varchar_enum,
)


# Portable JSON type: JSONB on PostgreSQL, JSON on SQLite
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Scenario(Base):
    __tablename__ = "scenario"

    __table_args__ = (
        CheckConstraint(
            "initial_stored_kwh >= 0",
            name="ck_scenario_initial_stored",
        ),
        CheckConstraint(
            "period_days >= 1",
            name="ck_scenario_period_days",
        ),
    )

    scenario_id = Column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    profile_id = Column(
        Uuid,
        ForeignKey("site_profile.profile_id"),
        nullable=False,
        index=True,
    )

    name = Column(
        String(100),
        nullable=True,
    )

    initial_stored_kwh = Column(
        Numeric(8, 2),
        nullable=False,
    )

    solar_day_type = Column(
        varchar_enum(
            SolarDayType,
            10,
            "ck_scenario_solar_day_type",
        ),
        nullable=False,
        server_default=SolarDayType.LOW_SUN.value,
    )

    period_days = Column(
        Integer,
        nullable=False,
    )

    outcome = Column(
        varchar_enum(Outcome, 25, "ck_scenario_outcome"),
        nullable=False,
    )

    check_results = Column(
        JSONType,
        nullable=False,
    )

    limiting_check = Column(
        varchar_enum(
            LimitingCheck,
            10,
            "ck_scenario_limiting_check",
        ),
        nullable=True,
    )

    monthly_revenue = Column(
        Numeric(12, 2),
        nullable=True,
    )

    revenue_basis = Column(
        varchar_enum(
            RevenueBasis,
            10,
            "ck_scenario_revenue_basis",
        ),
        nullable=True,
    )

    lowest_stored_kwh = Column(
        Numeric(10, 2),
        nullable=False,
    )

    data_label = Column(
        varchar_enum(DataLabel, 15, "ck_scenario_data_label"),
        nullable=False,
    )

    metrics = Column(
        JSONType,
        nullable=False,
    )

    simulation_trace = Column(
        JSONType,
        nullable=False,
    )

    input_snapshot = Column(
        JSONType,
        nullable=False,
    )

    created_by = Column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    profile = relationship(
        "SiteProfile",
        back_populates="scenarios",
    )

    business_links = relationship(
        "ScenarioBusiness",
        back_populates="scenario",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
