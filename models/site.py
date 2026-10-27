from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import relationship

from models.base import Base


class Site(Base):
    __tablename__ = "site"

    __table_args__ = (
        UniqueConstraint(
            "organisation_id",
            "site_name",
            name="uq_site_organisation_name",
        ),
    )

    site_id = Column(
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

    site_name = Column(
        String(100),
        nullable=False,
    )

    district = Column(
        String(100),
        nullable=False,
    )

    created_by = Column(
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
        back_populates="sites",
    )

    profiles = relationship(
        "SiteProfile",
        back_populates="site",
        order_by="SiteProfile.version",
    )

    businesses = relationship(
        "Business",
        back_populates="site",
    )
