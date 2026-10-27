
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import ConflictError
from models.user import User
from schemas.user import UserProfileResponse, UserProfileUpdateRequest


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
