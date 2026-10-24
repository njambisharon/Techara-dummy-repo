from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import Decision, varchar_enum


if TYPE_CHECKING:
    from models.business import Business
    from models.scenario import Scenario


class ScenarioBusiness(Base):
    __tablename__ = "scenario_business"
    __table_args__ = (
        CheckConstraint(
            "(decision IS NULL AND decided_by IS NULL AND decided_at IS NULL) "
            "OR (decision IS NOT NULL AND decided_by IS NOT NULL AND decided_at IS NOT NULL)",
            name="ck_scenario_business_decision_complete",
        ),
    )

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scenario.scenario_id", ondelete="CASCADE"),
        primary_key=True,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business.business_id"),
        primary_key=True,
        index=True,
    )
    decision: Mapped[Decision | None] = mapped_column(
        varchar_enum(Decision, 15, "ck_scenario_business_decision")
    )
    decision_note: Mapped[str | None] = mapped_column(String(255))
    decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    scenario: Mapped["Scenario"] = relationship(back_populates="business_links")
    business: Mapped["Business"] = relationship(back_populates="scenario_links")
