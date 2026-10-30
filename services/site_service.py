from core.exceptions import ConflictError, NotFoundError
from models.site import Site
from repositories.site_repository import site_repository


class SiteService:
    def create_site(self, db, data, current_user):
        if site_repository.get_by_name(
            db, current_user.organisation_id, data.site_name
        ):
            raise ConflictError("A site with this name already exists")
        site = Site(
            organisation_id=current_user.organisation_id,
            site_name=data.site_name,
            district=data.district,
            created_by=current_user.user_id,
        )
        return site_repository.create(db, site)

    def list_sites(self, db, current_user):
        return site_repository.list_for_organisation(db, current_user.organisation_id)

    def get_site(self, db, site_id, current_user):
        site = site_repository.get_for_organisation(
            db, site_id, current_user.organisation_id
        )
        if site is None:
            raise NotFoundError("Site not found")
        return site

    def update_site(self, db, site_id, data, current_user):
        site = self.get_site(db, site_id, current_user)
        changes = data.model_dump(exclude_unset=True, exclude_none=True)
        new_name = changes.get("site_name")
        if (
            new_name
            and new_name != site.site_name
            and site_repository.get_by_name(db, current_user.organisation_id, new_name)
        ):
            raise ConflictError("A site with this name already exists")
        for field, value in changes.items():
            setattr(site, field, value)
        return site_repository.save(db, site)


site_service = SiteService()
