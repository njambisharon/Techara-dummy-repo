from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from models.base import Base


class Reading(Base):
    __tablename__ = "reading"

    __table_args__ = (
        ForeignKeyConstraint(
            ["assignment_id", "business_id"],
            [
                "meter_assignment.assignment_id",
                "meter_assignment.business_id",
            ],
            name="fk_reading_assignment_business",
        ),
        UniqueConstraint(
            "assignment_id",
            "measured_at",
            name="uq_reading_assignment_measured_at",
        ),
        CheckConstraint(
            "voltage_v BETWEEN 0 AND 300",
            name="ck_reading_voltage",
        ),
        CheckConstraint(
            "current_a >= 0",
            name="ck_reading_current",
        ),
        CheckConstraint(
            "power_w >= 0",
            name="ck_reading_power",
        ),
        CheckConstraint(
            "energy_total_kwh >= 0",
            name="ck_reading_energy_total",
        ),
        Index(
            "ix_reading_business_measured_at",
            "business_id",
            "measured_at",
        ),
    )

    reading_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    assignment_id = Column(
        Uuid,
        ForeignKey("meter_assignment.assignment_id"),
        nullable=False,
    )

    business_id = Column(
        Uuid,
        ForeignKey("business.business_id"),
        nullable=False,
    )

    measured_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    voltage_v = Column(
        Numeric(6, 2),
        nullable=False,
    )

    current_a = Column(
        Numeric(7, 3),
        nullable=False,
    )

    power_w = Column(
        Numeric(9, 2),
        nullable=False,
    )

    energy_total_kwh = Column(
        Numeric(12, 4),
        nullable=False,
    )

    assignment = relationship(
        "MeterAssignment",
        back_populates="readings",
        foreign_keys="[Reading.assignment_id]",
        primaryjoin="Reading.assignment_id == MeterAssignment.assignment_id",
        viewonly=True,
    )
