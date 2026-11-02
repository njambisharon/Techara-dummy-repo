from sqlalchemy.orm import Session

from core.exceptions import NotFoundError
from models.user import User
from repositories.organisation_repository import organisation_repository
from schemas.organisation import OrganisationResponse


def get_current_organisation(
    db: Session,
    current_user: User,
) -> OrganisationResponse:
    organisation = organisation_repository.get_by_id(db, current_user.organisation_id)

    if organisation is None:
        raise NotFoundError("Organisation not found")

    return OrganisationResponse.model_validate(organisation)
