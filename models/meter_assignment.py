import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class MeterAssignment(Base):
    __tablename__ = "meter_assignment"
    __table_args__ = (
        UniqueConstraint("assignment_id", "business_id", name="uq_meter_assignment_id_business"),
        CheckConstraint("removed_at > installed_at", name="ck_meter_assignment_removed_after_installed"),
        Index(
            "uq_meter_assignment_open_device",
            "device_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_meter_assignment_open_business",
            "business_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sensor_device.device_id"), nullable=False, index=True
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("business.business_id"), nullable=False, index=True
    )
    device_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    installed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    device: Mapped["SensorDevice"] = relationship(back_populates="assignments")
    business: Mapped["Business"] = relationship(back_populates="assignments")
    readings: Mapped[list["Reading"]] = relationship(
        back_populates="assignment",
        foreign_keys="Reading.assignment_id",
        primaryjoin="MeterAssignment.assignment_id == Reading.assignment_id",
        viewonly=True,
    )