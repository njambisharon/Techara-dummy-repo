
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_roles
from models.enums import UserRole
from schemas.user import CreateFieldAgentRequest, CreateFieldAgentResponse
from services.user_service import create_field_agent
from database import get_db
from models.user import User
from schemas.user import CreateOperatorRequest, CreateOperatorResponse, UserProfileResponse, UserProfileUpdateRequest
from services.user_service import (
    create_field_agent,
    create_operator,
    get_current_user_profile,
    update_current_user_profile,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return get_current_user_profile(current_user)


@router.patch("/me", response_model=UserProfileResponse)
def update_my_profile(
    data: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return update_current_user_profile(db, current_user, data)

@router.post(
    "/field-agents",
    response_model=CreateFieldAgentResponse,
    status_code=201,
)
def create_field_agent_endpoint(
    data: CreateFieldAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR)),
) -> CreateFieldAgentResponse:
    return create_field_agent(db, current_user, data)

@router.post(
    "/operators",
    response_model=CreateOperatorResponse,
    status_code=201,
)
def create_operator_endpoint(
    data: CreateOperatorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.OPERATOR)),
) -> CreateOperatorResponse:
    return create_operator(db, current_user, data)