import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.enums import BusinessType, ConnectionStatus, StartupDataLabel, varchar_enum


class Business(Base):
    __tablename__ = "business"
    __table_args__ = (
        CheckConstraint("days_per_month BETWEEN 1 AND 31", name="ck_business_days_per_month"),
        CheckConstraint("startup_power_kw > 0", name="ck_business_startup_power"),
        CheckConstraint("startup_duration_s > 0", name="ck_business_startup_duration"),
        CheckConstraint(
            "(startup_power_kw IS NULL) = (startup_data_label IS NULL)", name="ck_business_startup_label_pair"
        ),
        CheckConstraint("jsonb_typeof(operating_hours) = 'object'", name="ck_business_operating_hours_shape"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("site.site_id"), nullable=False, index=True
    )
    logged_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    business_name: Mapped[str] = mapped_column(String(100), nullable=False)
    business_type: Mapped[BusinessType] = mapped_column(
        varchar_enum(BusinessType, 30, "ck_business_type"), nullable=False
    )
    owner_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_phone: Mapped[str | None] = mapped_column(String(20))
    connection_status: Mapped[ConnectionStatus] = mapped_column(
        varchar_enum(ConnectionStatus, 20, "ck_business_connection_status"),
        nullable=False,
        server_default=ConnectionStatus.PROSPECTIVE.value,
    )
    operating_hours: Mapped[dict] = mapped_column(JSONB, nullable=False)
    days_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    startup_power_kw: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    startup_duration_s: Mapped[int | None] = mapped_column(Integer)
    startup_data_label: Mapped[StartupDataLabel | None] = mapped_column(
        varchar_enum(StartupDataLabel, 15, "ck_business_startup_data_label")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    site: Mapped["Site"] = relationship(back_populates="businesses")
    assignments: Mapped[list["MeterAssignment"]] = relationship(back_populates="business")
    scenario_links: Mapped[list["ScenarioBusiness"]] = relationship(back_populates="business")