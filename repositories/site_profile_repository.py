from models.site_profile import SiteProfile
from sqlalchemy import func, select


class SiteProfileRepository:
    def create(self, db, profile):
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    def next_version(self, db, site_id):
        current = db.scalar(
            select(func.max(SiteProfile.version)).where(SiteProfile.site_id == site_id)
        )
        return (current or 0) + 1

    def list_for_site(self, db, site_id):
        return db.scalars(
            select(SiteProfile)
            .where(SiteProfile.site_id == site_id)
            .order_by(SiteProfile.version.desc())
        ).all()

    def latest_for_site(self, db, site_id):
        return db.scalar(
            select(SiteProfile)
            .where(SiteProfile.site_id == site_id)
            .order_by(SiteProfile.version.desc())
            .limit(1)
        )


site_profile_repository = SiteProfileRepository()
