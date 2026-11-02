from sqlalchemy.orm import Session

from models.organisation import Organisation


class OrganisationRepository:
    def get_by_id(self, db: Session, organisation_id) -> Organisation | None:
        return db.get(Organisation, organisation_id)


organisation_repository = OrganisationRepository()
