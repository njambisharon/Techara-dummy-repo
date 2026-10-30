from models.business import Business
from models.site import Site
from sqlalchemy import select


class BusinessRepository:
    def get_by_name(self, db, site_id, business_name):
        query = select(Business).where(
            Business.site_id == site_id,
            Business.business_name == business_name,
        )
        return db.scalar(query)

    def create(self, db, business):
        db.add(business)
        db.commit()
        db.refresh(business)
        return business

    def list_for_organisation(self, db, organisation_id):
        query = (
            select(Business)
            .join(Site, Business.site_id == Site.site_id)
            .where(Site.organisation_id == organisation_id)
            .order_by(Business.business_name)
        )
        return db.scalars(query).all()

    def get_for_organisation(self, db, business_id, organisation_id):
        query = (
            select(Business)
            .join(Site, Business.site_id == Site.site_id)
            .where(
                Business.business_id == business_id,
                Site.organisation_id == organisation_id,
            )
        )
        return db.scalar(query)

    def update(self, db, business):
        db.commit()
        db.refresh(business)
        return business

    def readings_for_business(self, db, business_id):
        from models.reading import Reading

        query = (
            select(Reading)
            .where(Reading.business_id == business_id)
            .order_by(Reading.measured_at)
        )
        return db.scalars(query).all()


business_repository = BusinessRepository()
