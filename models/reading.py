import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Reading(Base):
    __tablename__ = "reading"
    __table_args__ = (
        ForeignKeyConstraint(
            ["assignment_id", "business_id"],
            ["meter_assignment.assignment_id", "meter_assignment.business_id"],
            name="fk_reading_assignment_business",
        ),
        UniqueConstraint("assignment_id", "measured_at", name="uq_reading_assignment_measured_at"),
        CheckConstraint("voltage_v BETWEEN 0 AND 300", name="ck_reading_voltage"),
        CheckConstraint("current_a >= 0", name="ck_reading_current"),
        CheckConstraint("power_w >= 0", name="ck_reading_power"),
        CheckConstraint("energy_total_kwh >= 0", name="ck_reading_energy_total"),
        Index("ix_reading_business_measured_at", "business_id", "measured_at"),
    )

    reading_id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("meter_assignment.assignment_id"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.business_id"), nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    voltage_v: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    current_a: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    power_w: Mapped[Decimal] = mapped_column(Numeric(9, 2), nullable=False)
    energy_total_kwh: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    assignment: Mapped["MeterAssignment"] = relationship(
        back_populates="readings",
        foreign_keys=[assignment_id],
        primaryjoin="Reading.assignment_id == MeterAssignment.assignment_id",
        viewonly=True,
    )