from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.exceptions import NotFoundError, ConflictError
from models.user import User
from repositories.organisation_repository import organisation_repository
from schemas.organisation import OrganisationResponse, OrganisationUpdate


def get_current_organisation(
    db: Session,
    current_user: User,
) -> OrganisationResponse:
    organisation = organisation_repository.get_by_id(db, current_user.organisation_id)

    if organisation is None:
        raise NotFoundError("Organisation not found")

    return OrganisationResponse.model_validate(organisation)


def update_current_organisation(
    db: Session,
    current_user: User,
    data: OrganisationUpdate,
) -> OrganisationResponse:
    organisation = organisation_repository.get_by_id(db, current_user.organisation_id)

    if organisation is None:
        raise NotFoundError("Organisation not found")

    organisation.organisation_name = data.organisation_name.strip()

    if not organisation.organisation_name:
        raise ValueError("Organisation name cannot be empty")

    try:
        organisation = organisation_repository.update(db, organisation)
    except IntegrityError:
        db.rollback()
        raise ConflictError("Organisation name already exists")

    return OrganisationResponse.model_validate(organisation)
