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
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from models.base import Base
from models.enums import (
    BusinessType,
    ConnectionStatus,
    StartupDataLabel,
    varchar_enum,
)


JSONType = JSON().with_variant(JSONB(), "postgresql")


class Business(Base):
    __tablename__ = "business"

    __table_args__ = (
        UniqueConstraint("site_id", "business_name", name="uq_business_site_name"),
        CheckConstraint(
            "days_per_month BETWEEN 1 AND 31",
            name="ck_business_days_per_month",
        ),
        CheckConstraint(
            "startup_power_kw > 0",
            name="ck_business_startup_power",
        ),
        CheckConstraint(
            "startup_duration_s > 0",
            name="ck_business_startup_duration",
        ),
        CheckConstraint(
            "(startup_power_kw IS NULL) = (startup_data_label IS NULL)",
            name="ck_business_startup_label_pair",
        ),
    )

    business_id = Column(
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

    logged_by = Column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    business_name = Column(
        String(100),
        nullable=False,
    )

    business_type = Column(
        varchar_enum(BusinessType, 30, "ck_business_type"),
        nullable=False,
    )

    owner_first_name = Column(
        String(100),
        nullable=False,
    )

    owner_last_name = Column(
        String(100),
        nullable=False,
    )

    owner_phone = Column(
        String(20),
        nullable=True,
    )

    connection_status = Column(
        varchar_enum(
            ConnectionStatus,
            20,
            "ck_business_connection_status",
        ),
        nullable=False,
        server_default=ConnectionStatus.PROSPECTIVE.value,
    )

    operating_hours = Column(
        JSONType,
        nullable=False,
    )

    days_per_month = Column(
        Integer,
        nullable=False,
    )

    startup_power_kw = Column(
        Numeric(8, 2),
        nullable=True,
    )

    startup_duration_s = Column(
        Integer,
        nullable=True,
    )

    startup_data_label = Column(
        varchar_enum(
            StartupDataLabel,
            15,
            "ck_business_startup_data_label",
        ),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    site = relationship(
        "Site",
        back_populates="businesses",
    )

    assignments = relationship(
        "MeterAssignment",
        back_populates="business",
    )

    scenario_links = relationship(
        "ScenarioBusiness",
        back_populates="business",
    )
