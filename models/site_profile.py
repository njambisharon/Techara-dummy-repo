from sqlalchemy import (
    CheckConstraint,
    Column,
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
from sqlalchemy.orm import relationship

from models.base import Base


JSONType = JSON().with_variant(JSONB(), "postgresql")


class SiteProfile(Base):
    __tablename__ = "site_profile"

    __table_args__ = (
        UniqueConstraint(
            "site_id",
            "version",
            name="uq_site_profile_site_version",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_site_profile_version",
        ),
        CheckConstraint(
            "inverter_continuous_kw > 0",
            name="ck_site_profile_inverter_continuous",
        ),
        CheckConstraint(
            "inverter_surge_kw > 0",
            name="ck_site_profile_inverter_surge",
        ),
        CheckConstraint(
            "inverter_surge_duration_s > 0",
            name="ck_site_profile_inverter_surge_duration",
        ),
        CheckConstraint(
            "battery_nominal_kwh > 0",
            name="ck_site_profile_battery_nominal",
        ),
        CheckConstraint(
            "soc_min_percent BETWEEN 0 AND 100",
            name="ck_site_profile_soc_min_range",
        ),
        CheckConstraint(
            "soc_max_percent BETWEEN 0 AND 100",
            name="ck_site_profile_soc_max_range",
        ),
        CheckConstraint(
            "soc_min_percent < soc_max_percent",
            name="ck_site_profile_soc_order",
        ),
        CheckConstraint(
            "charge_efficiency > 0 AND charge_efficiency <= 1",
            name="ck_site_profile_charge_efficiency",
        ),
        CheckConstraint(
            "discharge_efficiency > 0 AND discharge_efficiency <= 1",
            name="ck_site_profile_discharge_efficiency",
        ),
        CheckConstraint(
            "max_charge_kw > 0",
            name="ck_site_profile_max_charge",
        ),
        CheckConstraint(
            "max_discharge_kw > 0",
            name="ck_site_profile_max_discharge",
        ),
        CheckConstraint(
            "tariff_per_kwh >= 0",
            name="ck_site_profile_tariff",
        ),
    )

    profile_id = Column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    site_id = Column(
        Uuid,
        ForeignKey("site.site_id"),
        nullable=False,
        index=True,
    )

    version = Column(
        Integer,
        nullable=False,
    )

    inverter_continuous_kw = Column(
        Numeric(8, 2),
        nullable=True,
    )

    inverter_surge_kw = Column(
        Numeric(8, 2),
        nullable=True,
    )

    inverter_surge_duration_s = Column(
        Integer,
        nullable=True,
    )

    battery_nominal_kwh = Column(
        Numeric(8, 2),
        nullable=False,
    )

    soc_min_percent = Column(
        Numeric(5, 2),
        nullable=False,
    )

    soc_max_percent = Column(
        Numeric(5, 2),
        nullable=False,
    )

    charge_efficiency = Column(
        Numeric(4, 3),
        nullable=False,
    )

    discharge_efficiency = Column(
        Numeric(4, 3),
        nullable=False,
    )

    max_charge_kw = Column(
        Numeric(8, 2),
        nullable=False,
    )

    max_discharge_kw = Column(
        Numeric(8, 2),
        nullable=False,
    )

    tariff_per_kwh = Column(
        Numeric(10, 2),
        nullable=False,
    )

    baseline_demand_kw = Column(
        JSONType,
        nullable=False,
    )

    solar_profile = Column(
        JSONType,
        nullable=False,
    )

    settings = Column(
        JSONType,
        nullable=False,
    )

    data_labels = Column(
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

    site = relationship(
        "Site",
        back_populates="profiles",
    )

    scenarios = relationship(
        "Scenario",
        back_populates="profile",
    )
