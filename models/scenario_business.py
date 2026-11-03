from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.base import Base
from models.enums import Decision, varchar_enum


class ScenarioBusiness(Base):
    __tablename__ = "scenario_business"

    __table_args__ = (
        CheckConstraint(
            "(decision IS NULL AND decided_by IS NULL AND decided_at IS NULL) "
            "OR (decision IS NOT NULL AND decided_by IS NOT NULL AND decided_at IS NOT NULL)",
            name="ck_scenario_business_decision_complete",
        ),
    )

    scenario_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scenario.scenario_id", ondelete="CASCADE"),
        primary_key=True,
    )

    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business.business_id"),
        primary_key=True,
        index=True,
    )

    decision = Column(
        varchar_enum(Decision, 15, "ck_scenario_business_decision"),
        nullable=True,
    )

    decision_note = Column(
        String(255),
        nullable=True,
    )

    decided_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=True,
    )

    decided_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    scenario = relationship(
        "Scenario",
        back_populates="business_links",
    )

    business = relationship(
        "Business",
        back_populates="scenario_links",
    )
