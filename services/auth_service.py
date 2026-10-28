from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import create_access_token
from models.enums import UserRole
from models.organisation import Organisation
from models.user import User
from repositories import auth_repository
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

    if auth_repository.get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    if auth_repository.get_organisation_by_name(db, organisation_name):
        raise HTTPException(
            status_code=409, detail="An organisation with this name already exists."
        )

    organisation = Organisation(organisation_name=organisation_name)

    user = User(
        organisation_id=organisation.organisation_id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=email,
        password_hash=password_hasher.hash(data.password),
        role=UserRole.OPERATOR,
    )

    try:
        auth_repository.create_organisation_and_operator(db, organisation, user)
    except IntegrityError:
        existing_user = auth_repository.get_user_by_email(db, email)
        if existing_user:
            return SignupResponse(message=SIGNUP_MESSAGE)

        existing_org = auth_repository.get_organisation_by_name(db, organisation_name)
        if existing_org:
            raise HTTPException(
                status_code=409, detail="An organisation with this name already exists."
            ) from None

        raise HTTPException(
            status_code=409,
            detail="The account could not be created with those details.",
        ) from None

    return SignupResponse(message=SIGNUP_MESSAGE)


def login(db: Session, data: LoginRequest) -> LoginResponse:
    identifier = data.identifier.strip()

    if "@" in identifier:
        user = auth_repository.get_user_by_email(db, identifier)
    else:
        user = auth_repository.get_user_by_phone(db, identifier)

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

    new_password_hash = password_hasher.hash(data.new_password)

    auth_repository.update_user_password(db, user, new_password_hash)

    return ChangePasswordResponse(message="Password changed successfully")
