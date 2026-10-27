from sqlalchemy import Column, DateTime, String, Uuid, func, text
from sqlalchemy.orm import relationship

from models.base import Base


class Organisation(Base):
    __tablename__ = "organisation"

    organisation_id = Column(
        Uuid,
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    organisation_name = Column(
        String(100),
        nullable=False,
        unique=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    users = relationship(
        "User",
        back_populates="organisation",
    )

    sites = relationship(
        "Site",
        back_populates="organisation",
    )

    sensor_devices = relationship(
        "SensorDevice",
        back_populates="organisation",
    )
