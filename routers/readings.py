import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import datetime
from core.dependencies import require_roles
from core.roles import ALL_ROLES
from database import get_db
from models.user import User
from schemas.reading import ReadingCreate, ReadingOut
from services.reading_service import reading_service

router = APIRouter(tags=["Readings"])


@router.get("/assignments/{assignment_id}/latest-reading", response_model=ReadingOut)
def latest_reading(
    assignment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return reading_service.get_latest(db, assignment_id)


from datetime import datetime

@router.get("/assignments/{assignment_id}/readings", response_model=list[ReadingOut])
def recent_readings(
    assignment_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=5000),
    since: datetime | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return reading_service.list_recent(db, assignment_id, limit, since)

@router.post(
    "/assignments/{assignment_id}/readings",
    response_model=ReadingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_reading(
    assignment_id: uuid.UUID,
    payload: ReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    return reading_service.create(db, assignment_id, payload)


@router.delete(
    "/assignments/{assignment_id}/readings/{reading_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reading(
    assignment_id: uuid.UUID,
    reading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
):
    reading_service.delete(db, assignment_id, reading_id)
