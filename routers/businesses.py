import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.dependencies import require_roles
from core.roles import ALL_ROLES
from database import get_db
from models.user import User
from schemas.businesses import (
    BusinessCreate,
    BusinessProfileRead,
    BusinessRead,
    BusinessUpdate,
)
from services.businesses import business_service

router = APIRouter(prefix="/businesses", tags=["Businesses"])


@router.post(
    "",
    response_model=BusinessRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business(
    data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return business_service.create_business(db, data, current_user)


@router.get(
    "",
    response_model=list[BusinessRead],
)
def list_businesses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return business_service.list_businesses(db, current_user)


@router.get(
    "/{business_id}",
    response_model=BusinessRead,
)
def get_business(
    business_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return business_service.get_business(db, business_id, current_user)


@router.patch(
    "/{business_id}",
    response_model=BusinessRead,
)
def update_business(
    business_id: uuid.UUID,
    data: BusinessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return business_service.update_business(
        db,
        business_id,
        data,
        current_user,
    )


@router.get(
    "/{business_id}/profile",
    response_model=BusinessProfileRead,
)
def get_business_profile(
    business_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return business_service.get_business_profile(
        db,
        business_id,
        current_user,
    )
