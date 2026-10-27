from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import SignupRequest, SignupResponse
from services.auth_service import signup

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
