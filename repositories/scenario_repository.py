from models.business import Business
from models.scenario import Scenario
from models.scenario_business import ScenarioBusiness
from models.site import Site
from models.site_profile import SiteProfile
from sqlalchemy import delete, select


class ScenarioRepository:
    def add(self, db, scenario, business_ids):
        db.add(scenario)
        db.flush()
        for business_id in business_ids:
            db.add(
                ScenarioBusiness(
                    scenario_id=scenario.scenario_id, business_id=business_id
                )
            )
        db.flush()
        return scenario

    def commit(self, db):
        db.commit()

    def rows_for_organisation(self, organisation_id):
        return (
            select(Scenario, SiteProfile.version, Site.site_id, Site.site_name)
            .join(SiteProfile, Scenario.profile_id == SiteProfile.profile_id)
            .join(Site, SiteProfile.site_id == Site.site_id)
            .where(Site.organisation_id == organisation_id)
        )

    def get_row(self, db, scenario_id, organisation_id):
        return db.execute(
            self.rows_for_organisation(organisation_id).where(
                Scenario.scenario_id == scenario_id
            )
        ).first()

    def list_rows(
        self,
        db,
        organisation_id,
        site_id=None,
        profile_id=None,
        business_id=None,
        scenario_ids=None,
    ):
        query = self.rows_for_organisation(organisation_id)
        if site_id is not None:
            query = query.where(Site.site_id == site_id)
        if profile_id is not None:
            query = query.where(Scenario.profile_id == profile_id)
        if business_id is not None:
            query = query.where(
                Scenario.scenario_id.in_(
                    select(ScenarioBusiness.scenario_id).where(
                        ScenarioBusiness.business_id == business_id
                    )
                )
            )
        if scenario_ids:
            query = query.where(Scenario.scenario_id.in_(scenario_ids))
        return db.execute(query.order_by(Scenario.created_at.desc())).all()

    def links_for(self, db, scenario_ids):
        return db.execute(
            select(ScenarioBusiness, Business.business_name)
            .join(Business, ScenarioBusiness.business_id == Business.business_id)
            .where(ScenarioBusiness.scenario_id.in_(scenario_ids))
            .order_by(Business.business_name)
        ).all()

    def has_decisions(self, db, scenario_id):
        found = db.scalar(
            select(ScenarioBusiness.scenario_id)
            .where(
                ScenarioBusiness.scenario_id == scenario_id,
                ScenarioBusiness.decision.is_not(None),
            )
            .limit(1)
        )
        return found is not None

    def delete(self, db, scenario):
        db.execute(
            delete(ScenarioBusiness).where(
                ScenarioBusiness.scenario_id == scenario.scenario_id
            )
        )
        db.delete(scenario)
        db.flush()


scenario_repository = ScenarioRepository()
