import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Site(Base):
    __tablename__ = "site"
    __table_args__ = (UniqueConstraint("organisation_id", "site_name", name="uq_site_organisation_name"),)

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisation.organisation_id"), nullable=False, index=True
    )
    site_name: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    organisation: Mapped["Organisation"] = relationship(back_populates="sites")
    profiles: Mapped[list["SiteProfile"]] = relationship(back_populates="site", order_by="SiteProfile.version")
    businesses: Mapped[list["Business"]] = relationship(back_populates="site")