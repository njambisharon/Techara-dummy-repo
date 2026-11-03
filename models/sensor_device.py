from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import relationship

from models.base import Base
from models.enums import DeviceStatus, varchar_enum


class SensorDevice(Base):
    __tablename__ = "sensor_device"

    device_id = Column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    organisation_id = Column(
        Uuid,
        ForeignKey("organisation.organisation_id"),
        nullable=False,
        index=True,
    )

    device_serial = Column(
        String(50),
        nullable=False,
        unique=True,
    )

    status = Column(
        varchar_enum(
            DeviceStatus,
            15,
            "ck_sensor_device_status",
        ),
        nullable=False,
        server_default=DeviceStatus.ACTIVE.value,
    )

    registered_by = Column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    organisation = relationship(
        "Organisation",
        back_populates="sensor_devices",
    )

    assignments = relationship(
        "MeterAssignment",
        back_populates="device",
    )
