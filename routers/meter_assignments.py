import uuid

from core.dependencies import require_roles
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from models.enums import UserRole
from models.user import User
from repositories.meter_assignment_repository import meter_assignment_repository
from schemas.meter_assignment import (
    MeterAssignmentCreate,
    MeterAssignmentCreated,
    MeterAssignmentRead,
    MeterAssignmentRemove,
)
from services.meter_assignment_service import meter_assignment_service
from sqlalchemy.orm import Session

FIELD_AGENT_ONLY = (UserRole.FIELD_AGENT,)
ALL_ROLES = (UserRole.OPERATOR, UserRole.FIELD_AGENT)

router = APIRouter(prefix="/assignments", tags=["Meter assignments"])


@router.post(
    "",
    response_model=MeterAssignmentCreated,
    status_code=status.HTTP_201_CREATED,
)
def install_meter(
    data: MeterAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return meter_assignment_service.install_meter(db, data, current_user)


@router.post("/{assignment_id}/remove", response_model=MeterAssignmentRead)
def remove_meter(
    assignment_id: uuid.UUID,
    data: MeterAssignmentRemove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*FIELD_AGENT_ONLY)),
):
    return meter_assignment_service.remove_meter(db, assignment_id, data, current_user)


@router.get("", response_model=list[MeterAssignmentRead])
def list_assignments(
    business_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    open_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return meter_assignment_service.list_assignments(
        db, current_user, business_id, device_id, open_only
    )


@router.get("/{assignment_id}", response_model=MeterAssignmentRead)
def get_meter_assignment(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    assignment = meter_assignment_repository.get_for_organisation(
        db, assignment_id, current_user.organisation_id
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="Meter assignment not found")
    return assignment
