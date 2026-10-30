import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas.reading import ReadingOut
from services.reading_service import reading_service

router = APIRouter(tags=["Readings"])


@router.get("/assignments/{assignment_id}/latest-reading", response_model=ReadingOut)
def latest_reading(assignment_id: uuid.UUID, db: Session = Depends(get_db)):
    return reading_service.get_latest(db, assignment_id)


@router.get("/assignments/{assignment_id}/readings", response_model=list[ReadingOut])
def recent_readings(
    assignment_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return reading_service.list_recent(db, assignment_id, limit)
