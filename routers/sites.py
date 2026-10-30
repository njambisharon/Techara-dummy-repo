import uuid

from core.roles import ALL_ROLES, OPERATOR_ONLY
from database import get_db
from dependencies import require_roles
from fastapi import APIRouter, Depends, status
from models.user import User
from schemas.site import SiteCreate, SiteRead, SiteUpdate
from schemas.site_profile import SpareCapacityRead
from services.site_profile_service import site_profile_service
from services.site_service import site_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.post("", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def create_site(
    data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_service.create_site(db, data, current_user)


@router.get("", response_model=list[SiteRead])
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return site_service.list_sites(db, current_user)


@router.get("/{site_id}", response_model=SiteRead)
def get_site(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return site_service.get_site(db, site_id, current_user)


@router.patch("/{site_id}", response_model=SiteRead)
def update_site(
    site_id: uuid.UUID,
    data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_service.update_site(db, site_id, data, current_user)


@router.get("/{site_id}/spare-capacity", response_model=SpareCapacityRead)
def get_spare_capacity(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_profile_service.get_spare_capacity(db, site_id, current_user)
