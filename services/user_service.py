import secrets
import string

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, ForbiddenError
from models.enums import UserRole
from models.user import User
from schemas.user import CreateFieldAgentRequest, CreateOperatorRequest, UserProfileResponse, UserProfileUpdateRequest


def get_current_user_profile(current_user: User) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


def update_current_user_profile(
    db: Session,
    current_user: User,
    data: UserProfileUpdateRequest,
) -> UserProfileResponse:
    updates = data.model_dump(exclude_unset=True)

    if "email" in updates:
        duplicate_email = db.scalar(
            select(User).where(
                User.email == str(updates["email"]),
                User.user_id != current_user.user_id,
            )
        )
        if duplicate_email:
            raise ConflictError("Email address is already in use")

    if "phone_number" in updates:
        duplicate_phone = db.scalar(
            select(User).where(
                User.phone_number == updates["phone_number"],
                User.user_id != current_user.user_id,
            )
        )
        if duplicate_phone:
            raise ConflictError("Phone number is already in use")

    for field, value in updates.items():
        if field == "email" and value is not None:
            value = str(value)
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return UserProfileResponse.model_validate(current_user)

password_hasher = PasswordHash.recommended()


def create_field_agent(db: Session, current_user: User, data: CreateFieldAgentRequest) -> dict:
    if current_user.role != UserRole.OPERATOR:
        raise ForbiddenError("Only mini-grid operators can create field operators")

    existing_phone = db.scalar(
        select(User).where(User.phone_number == data.phone_number)
    )
    if existing_phone:
        raise ConflictError("This phone number is already registered")

    alphabet = string.ascii_letters + string.digits
    temporary_password = "".join(secrets.choice(alphabet) for _ in range(12))

    field_agent = User(
        organisation_id=current_user.organisation_id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone_number=data.phone_number,
        password_hash=password_hasher.hash(temporary_password),
        role=UserRole.FIELD_AGENT,
        must_change_password=True,
        created_by=current_user.user_id,
    )

    try:
        db.add(field_agent)
        db.commit()
        db.refresh(field_agent)
    except IntegrityError:
        db.rollback()
        raise ConflictError("This phone number is already registered") from None

    return {
        "user": UserProfileResponse.model_validate(field_agent),
        "temporary_password": temporary_password,
        "message": "Field operator account created. Share the temporary password securely.",
    }

def create_operator(
    db: Session,
    current_user: User,
    data: CreateOperatorRequest,
) -> dict:
    if current_user.role != UserRole.OPERATOR:
        raise ForbiddenError("Only mini-grid operators can create operator accounts")

    email = str(data.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email.ilike(email))
    )
    if existing_user:
        raise ConflictError("This email address is already registered")

    alphabet = string.ascii_letters + string.digits
    temporary_password = "".join(
        secrets.choice(alphabet) for _ in range(12)
    )

    operator = User(
        organisation_id=current_user.organisation_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=email,
        password_hash=password_hasher.hash(temporary_password),
        role=UserRole.OPERATOR,
        must_change_password=True,
        created_by=current_user.user_id,
    )

    try:
        db.add(operator)
        db.commit()
        db.refresh(operator)
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            "This email address is already registered"
        ) from None

    return {
        "user": UserProfileResponse.model_validate(operator),
        "temporary_password": temporary_password,
        "message": "Operator account created. Share the temporary password securely.",
    }

def list_organisation_users(
    db: Session,
    current_user: User,
) -> list[UserProfileResponse]:
    users = db.scalars(
        select(User)
        .where(User.organisation_id == current_user.organisation_id)
        .order_by(User.created_at.desc())
    ).all()

    return [
        UserProfileResponse.model_validate(user)
        for user in users
    ]