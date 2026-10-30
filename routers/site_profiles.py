import uuid

from core.roles import OPERATOR_ONLY
from database import get_db
from dependencies import require_roles
from fastapi import APIRouter, Depends, status
from models.user import User
from schemas.site_profile import (
    MonitoringImport,
    MonitoringImportRead,
    SiteProfileCreate,
    SiteProfileRead,
)
from services.site_profile_service import site_profile_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sites/{site_id}/profiles", tags=["Site profiles"])


@router.post("", response_model=SiteProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    site_id: uuid.UUID,
    data: SiteProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_profile_service.create_profile(db, site_id, data, current_user)


@router.get("", response_model=list[SiteProfileRead])
def list_profiles(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_profile_service.list_profiles(db, site_id, current_user)


@router.get("/latest", response_model=SiteProfileRead)
def get_latest_profile(
    site_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_profile_service.get_latest_profile(db, site_id, current_user)


@router.post("/import", response_model=MonitoringImportRead)
def import_monitoring_export(
    site_id: uuid.UUID,
    data: MonitoringImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return site_profile_service.import_monitoring_export(
        db, site_id, data, current_user
    )
