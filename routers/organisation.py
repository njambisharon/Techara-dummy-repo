from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.dependencies import require_password_changed
from database import get_db
from models.user import User
from schemas.organisation import OrganisationResponse
from services.organisation_service import get_current_organisation

router = APIRouter(prefix="/organisation", tags=["Organisation"])


@router.get("", response_model=OrganisationResponse)
def get_organisation(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
) -> OrganisationResponse:
    return get_current_organisation(db, current_user)
