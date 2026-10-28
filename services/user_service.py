import secrets
import string

from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from models.enums import UserRole
from models.user import User
from repositories.user_repository import user_repository
from schemas.user import (
    CreateFieldAgentRequest,
    CreateOperatorRequest,
    UpdateUserStatusRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
)


password_hasher = PasswordHash.recommended()


def get_current_user_profile(current_user: User) -> UserProfileResponse:
    return UserProfileResponse.model_validate(current_user)


def update_current_user_profile(
    db: Session,
    current_user: User,
    data: UserProfileUpdateRequest,
) -> UserProfileResponse:
    updates = data.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] is not None:
        email = str(updates["email"]).strip().lower()
        duplicate_email = user_repository.get_by_email(db, email)

        if duplicate_email and duplicate_email.user_id != current_user.user_id:
            raise ConflictError("Email address is already in use")

        updates["email"] = email

    if "phone_number" in updates and updates["phone_number"] is not None:
        duplicate_phone = user_repository.get_by_phone(db, updates["phone_number"])

        if duplicate_phone and duplicate_phone.user_id != current_user.user_id:
            raise ConflictError("Phone number is already in use")

    for field, value in updates.items():
        setattr(current_user, field, value)

    try:
        user_repository.save(db, current_user)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email address or phone number is already in use") from None

    return UserProfileResponse.model_validate(current_user)


def create_field_agent(
    db: Session,
    current_user: User,
    data: CreateFieldAgentRequest,
) -> dict:
    if current_user.role != UserRole.OPERATOR:
        raise ForbiddenError("Only mini-grid operators can create field operators")

    existing_phone = user_repository.get_by_phone(db, data.phone_number)
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
        user_repository.create(db, field_agent)
    except IntegrityError:
        db.rollback()
        raise ConflictError("This phone number is already registered") from None

    return {
        "user": UserProfileResponse.model_validate(field_agent),
        "temporary_password": temporary_password,
        "message": (
            "Field operator account created. Share the temporary password securely."
        ),
    }


def create_operator(
    db: Session,
    current_user: User,
    data: CreateOperatorRequest,
) -> dict:
    if current_user.role != UserRole.OPERATOR:
        raise ForbiddenError("Only mini-grid operators can create operator accounts")

    email = str(data.email).strip().lower()
    existing_user = user_repository.get_by_email(db, email)

    if existing_user:
        raise ConflictError("This email address is already registered")

    alphabet = string.ascii_letters + string.digits
    temporary_password = "".join(secrets.choice(alphabet) for _ in range(12))

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
        user_repository.create(db, operator)
    except IntegrityError:
        db.rollback()
        raise ConflictError("This email address is already registered") from None

    return {
        "user": UserProfileResponse.model_validate(operator),
        "temporary_password": temporary_password,
        "message": ("Operator account created. Share the temporary password securely."),
    }


def list_organisation_users(
    db: Session,
    current_user: User,
) -> list[UserProfileResponse]:
    users = user_repository.list_for_organisation(db, current_user.organisation_id)
    return [UserProfileResponse.model_validate(user) for user in users]


def update_user_status(
    db: Session,
    current_user: User,
    user_id,
    data: UpdateUserStatusRequest,
) -> dict:
    if current_user.role != UserRole.OPERATOR:
        raise ForbiddenError("Only mini-grid operators can update user status")

    user = user_repository.get_by_id_and_organisation(
        db, user_id, current_user.organisation_id
    )

    if user is None:
        raise NotFoundError("User not found in your organisation")

    if user.user_id == current_user.user_id and not data.is_active:
        raise ForbiddenError("You cannot deactivate your own account")

    user.is_active = data.is_active

    try:
        user_repository.save(db, user)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Could not update user status") from None

    status_message = "activated" if user.is_active else "deactivated"

    return {
        "message": f"User {status_message} successfully",
        "user": UserProfileResponse.model_validate(user),
    }
