from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from core.exceptions import ConflictError
from models.organisation import Organisation
from models.user import User
from models.enums import UserRole
from schemas.auth import SignupRequest, SignupResponse

password_hasher = PasswordHash.recommended()

SIGNUP_MESSAGE = (
    "If registration can be completed, the account has been created."
)


def signup(db: Session, data: SignupRequest) -> SignupResponse:
    email = str(data.email).strip().lower()
    organisation_name = data.organisation_name.strip()

    existing_user = db.scalar(
        select(User).where(func.lower(User.email) == email)
    )

    if existing_user:
        return SignupResponse(message=SIGNUP_MESSAGE)

    existing_org = db.scalar(
        select(Organisation).where(
            func.lower(Organisation.organisation_name)
            == organisation_name.lower()
        )
    )

    if existing_org:
        raise ConflictError("An organisation with this name already exists.")

    try:
        organisation = Organisation(organisation_name=organisation_name)
        db.add(organisation)
        db.flush()

        user = User(
            organisation_id=organisation.organisation_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=email,
            password_hash=password_hasher.hash(data.password),
            role=UserRole.OPERATOR,
        )
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_user = db.scalar(
            select(User).where(func.lower(User.email) == email)
        )
        if existing_user:
            return SignupResponse(message=SIGNUP_MESSAGE)

        raise ConflictError(
            "The account could not be created with those details."
        ) from None
    except Exception:
        db.rollback()
        raise

    return SignupResponse(message=SIGNUP_MESSAGE)
