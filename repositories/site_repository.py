from models.site import Site
from sqlalchemy import select


class SiteRepository:
    def create(self, db, site):
        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    def get_by_name(self, db, organisation_id, site_name):
        return db.scalar(
            select(Site).where(
                Site.organisation_id == organisation_id,
                Site.site_name == site_name,
            )
        )

    def list_for_organisation(self, db, organisation_id):
        return db.scalars(
            select(Site)
            .where(Site.organisation_id == organisation_id)
            .order_by(Site.site_name)
        ).all()

    def get_for_organisation(self, db, site_id, organisation_id):
        return db.scalar(
            select(Site).where(
                Site.site_id == site_id,
                Site.organisation_id == organisation_id,
            )
        )

    def save(self, db, site):
        db.commit()
        db.refresh(site)
        return site


site_repository = SiteRepository()
