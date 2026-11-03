from sqlalchemy.orm import Session

from models.organisation import Organisation


class OrganisationRepository:
    def get_by_id(self, db: Session, organisation_id) -> Organisation | None:
        return db.get(Organisation, organisation_id)

    def update(self, db: Session, organisation: Organisation) -> Organisation:
        db.add(organisation)
        db.commit()
        db.refresh(organisation)
        return organisation


organisation_repository = OrganisationRepository()
