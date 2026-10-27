from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from models.user import User
from schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    SignupRequest,
    SignupResponse,
)
from services.auth_service import change_password, login, signup

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup_endpoint(
    data: SignupRequest,
    db: Session = Depends(get_db),
) -> SignupResponse:
    return signup(db, data)


@router.post("/login", response_model=LoginResponse)
def login_endpoint(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    return login(db, data)


@router.patch(
    "/change-password",
    response_model=ChangePasswordResponse,
)
def change_password_endpoint(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChangePasswordResponse:
    return change_password(db, current_user, data)
