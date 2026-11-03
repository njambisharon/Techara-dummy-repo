from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import relationship

from models.base import Base


class MeterAssignment(Base):
    __tablename__ = "meter_assignment"

    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "business_id",
            name="uq_meter_assignment_id_business",
        ),
        CheckConstraint(
            "removed_at > installed_at",
            name="ck_meter_assignment_removed_after_installed",
        ),
        Index(
            "uq_meter_assignment_open_device",
            "device_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
            sqlite_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_meter_assignment_open_business",
            "business_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
            sqlite_where=text("removed_at IS NULL"),
        ),
    )

    assignment_id = Column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    device_id = Column(
        Uuid,
        ForeignKey("sensor_device.device_id"),
        nullable=False,
        index=True,
    )

    business_id = Column(
        Uuid,
        ForeignKey("business.business_id"),
        nullable=False,
        index=True,
    )

    device_token_hash = Column(
        String(255),
        nullable=False,
    )

    installed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    removed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    installed_by = Column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
    )

    device = relationship(
        "SensorDevice",
        back_populates="assignments",
    )

    business = relationship(
        "Business",
        back_populates="assignments",
    )

    readings = relationship(
        "Reading",
        back_populates="assignment",
        foreign_keys="[Reading.assignment_id]",
        primaryjoin="MeterAssignment.assignment_id == Reading.assignment_id",
        viewonly=True,
    )
