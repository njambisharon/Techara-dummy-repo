from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
from models.enums import UserRole, varchar_enum


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "(role = 'field_agent' AND phone_number IS NOT NULL) "
            "OR (role = 'operator' AND email IS NOT NULL)",
            name="ck_users_login_identifier",
        ),
    )

    user_id = Column(
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

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    email = Column(String(100), unique=True)
    phone_number = Column(String(20), unique=True)

    password_hash = Column(String(255), nullable=False)

    role = Column(
        varchar_enum(UserRole, 20, "ck_users_role"),
        nullable=False,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    must_change_password = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    created_by = Column(
        Uuid,
        ForeignKey("users.user_id"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    organisation = relationship(
        "Organisation",
        back_populates="users",
    )
