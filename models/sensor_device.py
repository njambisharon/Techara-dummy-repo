import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import DeviceStatus, varchar_enum


class SensorDevice(Base):
    __tablename__ = "sensor_device"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.organisation_id"), nullable=False, index=True
    )
    device_serial: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    model: Mapped[str] = mapped_column(String(50), nullable=False, server_default="PZEM-004T")
    status: Mapped[DeviceStatus] = mapped_column(
        varchar_enum(DeviceStatus, 15, "ck_sensor_device_status"),
        nullable=False,
        server_default=DeviceStatus.ACTIVE.value,
    )
    registered_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    organisation: Mapped["Organisation"] = relationship(back_populates="sensor_devices")
    assignments: Mapped[list["MeterAssignment"]] = relationship(back_populates="device")