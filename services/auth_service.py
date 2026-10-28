from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from core.exceptions import ConflictError
from core.security import create_access_token
from models.organisation import Organisation
from models.user import User
from models.enums import UserRole
from schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)

password_hasher = PasswordHash.recommended()

SIGNUP_MESSAGE = "If registration can be completed, the account has been created."


def signup(db: Session, data: SignupRequest) -> SignupResponse:
    email = str(data.email).strip().lower()
    organisation_name = data.organisation_name.strip()

    existing_user = db.scalar(select(User).where(func.lower(User.email) == email))

    if existing_user:
        return SignupResponse(message=SIGNUP_MESSAGE)

    existing_org = db.scalar(
        select(Organisation).where(
            func.lower(Organisation.organisation_name) == organisation_name.lower()
        )
    )

    if existing_org:
        raise ConflictError("An organisation with this name already exists.")

    try:
        organisation = Organisation(organisation_name=organisation_name)
        db.add(organisation)
        db.flush()

        user = User(
            organisation_id=organisation.organisation_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=email,
            password_hash=password_hasher.hash(data.password),
            role=UserRole.OPERATOR,
        )
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_user = db.scalar(select(User).where(func.lower(User.email) == email))
        if existing_user:
            return SignupResponse(message=SIGNUP_MESSAGE)

        raise ConflictError(
            "The account could not be created with those details."
        ) from None
    except Exception:
        db.rollback()
        raise

    return SignupResponse(message=SIGNUP_MESSAGE)


def login(db: Session, data: LoginRequest) -> LoginResponse:
    identifier = data.identifier.strip()

    if "@" in identifier:
        user = db.scalar(
            select(User).where(func.lower(User.email) == identifier.lower())
        )
    else:
        user = db.scalar(select(User).where(User.phone_number == identifier))

    if (
        user is None
        or not user.is_active
        or not password_hasher.verify(data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(
        user.user_id,
        user.role.value,
        user.organisation_id,
    )

    return LoginResponse(access_token=token)


def change_password(
    db: Session,
    user: User,
    data: ChangePasswordRequest,
) -> ChangePasswordResponse:
    if not password_hasher.verify(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    user.password_hash = password_hasher.hash(data.new_password)
    user.must_change_password = False
    db.commit()

    return ChangePasswordResponse(message="Password changed successfully")
