from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


if TYPE_CHECKING:
    from models.sensor_device import SensorDevice
    from models.site import Site
    from models.user import User


class Organisation(Base):
    __tablename__ = "organisation"

    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organisation_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    users: Mapped[list["User"]] = relationship(back_populates="organisation")
    sites: Mapped[list["Site"]] = relationship(back_populates="organisation")
    sensor_devices: Mapped[list["SensorDevice"]] = relationship(
        back_populates="organisation"
    )
