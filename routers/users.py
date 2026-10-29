from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from core.dependencies import get_current_user, require_roles
from database import get_db
from models.enums import UserRole
from models.user import User
from schemas.user import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserStatusRequest,
    UpdateUserStatusResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
)
from services.user_service import (
    create_user,
    get_current_user_profile,
    list_organisation_users,
    update_current_user_profile,
    update_user_status,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return get_current_user_profile(current_user)


@router.get("/", response_model=list[UserProfileResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR)),
) -> list[UserProfileResponse]:
    return list_organisation_users(db, current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return update_current_user_profile(db, current_user, data)


@router.post("/", response_model=CreateUserResponse, status_code=201)
def create_user_endpoint(
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR)),
) -> CreateUserResponse:
    return create_user(db, current_user, data)


@router.patch(
    "/{user_id}/status",
    response_model=UpdateUserStatusResponse,
)
def update_user_status_endpoint(
    user_id: UUID,
    data: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR)),
) -> UpdateUserStatusResponse:
    return update_user_status(db, current_user, user_id, data)
