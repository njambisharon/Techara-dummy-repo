from decimal import Decimal

from core.exceptions import ConflictError, InvalidDataError, NotFoundError
from engine.evaluator import rank_key, run_assessment
from engine.hours import open_hours
from models.enums import DataLabel, LimitingCheck, Outcome, RevenueBasis, SolarDayType
from models.scenario import Scenario
from repositories.scenario_repository import scenario_repository
from repositories.site_profile_repository import site_profile_repository
from services.business_service import business_service
from services.site_profile_service import to_engine_site


def enum_value(value):
    return getattr(value, "value", value)


class ScenarioService:
    def get_profile(self, db, profile_id, current_user):
        profile = site_profile_repository.get_for_organisation(
            db, profile_id, current_user.organisation_id
        )
        if profile is None:
            raise NotFoundError("Site profile not found")
        return profile

    def get_site_profile(self, db, site_id, current_user):
        latest = site_profile_repository.latest_for_site(db, site_id)
        if latest is None:
            raise NotFoundError("Site profile not found")
        return self.get_profile(db, latest.profile_id, current_user)

    def load_businesses(self, db, business_ids, current_user):
        if len(set(business_ids)) != len(business_ids):
            raise InvalidDataError("A business can only be added to a scenario once")
        found = {
            business.business_id: business
            for business in scenario_repository.businesses_for_organisation(
                db, business_ids, current_user.organisation_id
            )
        }
        if len(found) != len(business_ids):
            raise NotFoundError("Business not found")
        return [found[business_id] for business_id in business_ids]

    def check_initial_stored(self, profile, initial_stored_kwh):
        nominal = float(profile.battery_nominal_kwh)
        low = nominal * float(profile.soc_min_percent) / 100
        high = nominal * float(profile.soc_max_percent) / 100
        if not low - 1e-6 <= float(initial_stored_kwh) <= high + 1e-6:
            raise InvalidDataError(
                f"initial_stored_kwh must be between {low:.2f} and {high:.2f} kWh for this profile"
            )

    def initial_from_percent(self, profile, percent):
        low = float(profile.soc_min_percent)
        high = float(profile.soc_max_percent)
        chosen = (low + high) / 2 if percent is None else float(percent)
        if not low - 1e-6 <= chosen <= high + 1e-6:
            raise InvalidDataError(
                f"initial_soc_percent must be between {low:.0f} and {high:.0f} for site {profile.site_id}"
            )
        nominal = float(profile.battery_nominal_kwh)
        return Decimal(str(round(nominal * chosen / 100, 2)))

    def engine_businesses(self, db, businesses, min_days):
        prepared = []
        short = []
        for business in businesses:
            profile = business_service.build_profile(db, business, min_days)
            if not profile["is_observed"]:
                short.append(
                    f"{business.business_name} ({profile['observed_days']} days)"
                )
                continue
            prepared.append(
                {
                    "business_id": str(business.business_id),
                    "business_name": business.business_name,
                    "business_type": enum_value(business.business_type),
                    "average_kw": profile["average_kw"],
                    "peak_kw": profile["peak_kw"],
                    "open_hours": open_hours(business.operating_hours),
                    "operating_hours": business.operating_hours,
                    "days_per_month": business.days_per_month,
                    "startup_power_kw": None
                    if business.startup_power_kw is None
                    else float(business.startup_power_kw),
                    "startup_duration_s": business.startup_duration_s,
                    "startup_data_label": enum_value(business.startup_data_label),
                    "data_label": "observed",
                    "reading_count": profile["reading_count"],
                    "observed_days": profile["observed_days"],
                    "first_measured_at": profile["first_measured_at"].isoformat(),
                    "last_measured_at": profile["last_measured_at"].isoformat(),
                }
            )
        if short:
            raise InvalidDataError(
                f"Every business needs at least {min_days} observed days of readings: "
                + ", ".join(short)
            )
        return prepared

    def build_scenario(self, db, profile, businesses, values, current_user):
        site = to_engine_site(profile)
        prepared = self.engine_businesses(
            db, businesses, int(site["settings"]["min_observed_days"])
        )
        flags = [
            {
                "business_id": str(business.business_id),
                "type": "not_nearest_site",
                "message": f"{business.business_name} is logged at another site of your organisation",
            }
            for business in businesses
            if business.site_id != profile.site_id
        ]
        solar_day_type = enum_value(values["solar_day_type"])
        result = run_assessment(
            site,
            prepared,
            float(values["initial_stored_kwh"]),
            solar_day_type,
            values["period_days"],
            flags,
        )
        snapshot = {
            "profile_id": str(profile.profile_id),
            "profile_version": profile.version,
            "site_id": str(profile.site_id),
            "solar_day_type": solar_day_type,
            "initial_stored_kwh": float(values["initial_stored_kwh"]),
            "period_days": values["period_days"],
            "site": site,
            "businesses": [
                {key: value for key, value in item.items() if key != "open_hours"}
                for item in prepared
            ],
        }
        scenario = Scenario(
            profile_id=profile.profile_id,
            name=values.get("name"),
            initial_stored_kwh=values["initial_stored_kwh"],
            solar_day_type=SolarDayType(solar_day_type),
            period_days=values["period_days"],
            outcome=Outcome(result["outcome"]),
            check_results=result["check_results"],
            limiting_check=LimitingCheck(result["limiting_check"])
            if result["limiting_check"]
            else None,
            monthly_revenue=Decimal(str(result["monthly_revenue"])),
            revenue_basis=RevenueBasis(result["revenue_basis"]),
            lowest_stored_kwh=Decimal(str(round(result["lowest_stored_kwh"], 2))),
            data_label=DataLabel(result["data_label"]),
            metrics=result["metrics"],
            simulation_trace=result["simulation_trace"],
            input_snapshot=snapshot,
            created_by=current_user.user_id,
        )
        return scenario_repository.add(
            db, scenario, [business.business_id for business in businesses]
        )

    def create_scenario(self, db, data, current_user):
        profile = self.get_profile(db, data.profile_id, current_user)
        self.check_initial_stored(profile, data.initial_stored_kwh)
        businesses = self.load_businesses(db, data.business_ids, current_user)
        scenario = self.build_scenario(
            db, profile, businesses, data.model_dump(), current_user
        )
        scenario_repository.commit(db)
        return self.get_scenario(db, scenario.scenario_id, current_user)

    def compare_sites(self, db, data, current_user):
        if len(set(data.site_ids)) != len(data.site_ids):
            raise InvalidDataError("A site can only be compared once")
        profiles = [
            self.get_site_profile(db, site_id, current_user)
            for site_id in data.site_ids
        ]
        starts = [
            self.initial_from_percent(profile, data.initial_soc_percent)
            for profile in profiles
        ]
        businesses = self.load_businesses(db, data.business_ids, current_user)
        values = data.model_dump()
        scenario_ids = []
        for profile, start in zip(profiles, starts):
            values["initial_stored_kwh"] = start
            scenario = self.build_scenario(
                db, profile, businesses, values, current_user
            )
            scenario_ids.append(scenario.scenario_id)
        scenario_repository.commit(db)
        return self.list_scenarios(db, current_user, scenario_ids=scenario_ids)

    def summaries(self, db, rows):
        links = {}
        for link, business_name in scenario_repository.links_for(
            db, [row[0].scenario_id for row in rows]
        ):
            links.setdefault(link.scenario_id, []).append(
                {
                    "business_id": link.business_id,
                    "business_name": business_name,
                    "decision": link.decision,
                    "decision_note": link.decision_note,
                    "decided_by": link.decided_by,
                    "decided_at": link.decided_at,
                }
            )
        return [
            {
                "scenario_id": scenario.scenario_id,
                "profile_id": scenario.profile_id,
                "profile_version": version,
                "site_id": site_id,
                "site_name": site_name,
                "name": scenario.name,
                "solar_day_type": scenario.solar_day_type,
                "period_days": scenario.period_days,
                "outcome": scenario.outcome,
                "limiting_check": scenario.limiting_check,
                "monthly_revenue": scenario.monthly_revenue,
                "revenue_basis": scenario.revenue_basis,
                "lowest_stored_kwh": scenario.lowest_stored_kwh,
                "data_label": scenario.data_label,
                "created_by": scenario.created_by,
                "created_at": scenario.created_at,
                "businesses": links.get(scenario.scenario_id, []),
            }
            for scenario, version, site_id, site_name in rows
        ]

    def get_row(self, db, scenario_id, current_user):
        row = scenario_repository.get_row(db, scenario_id, current_user.organisation_id)
        if row is None:
            raise NotFoundError("Scenario not found")
        return row

    def get_scenario(self, db, scenario_id, current_user):
        row = self.get_row(db, scenario_id, current_user)
        scenario = row[0]
        return {
            **self.summaries(db, [row])[0],
            "initial_stored_kwh": scenario.initial_stored_kwh,
            "check_results": scenario.check_results,
            "metrics": scenario.metrics,
            "simulation_trace": scenario.simulation_trace,
            "input_snapshot": scenario.input_snapshot,
        }

    def list_scenarios(
        self,
        db,
        current_user,
        site_id=None,
        profile_id=None,
        business_id=None,
        scenario_ids=None,
        order="rank",
    ):
        rows = scenario_repository.list_rows(
            db,
            current_user.organisation_id,
            site_id,
            profile_id,
            business_id,
            scenario_ids,
        )
        items = self.summaries(db, rows)
        ranked = sorted(
            items,
            key=lambda item: rank_key(
                enum_value(item["outcome"]),
                item["monthly_revenue"],
                item["lowest_stored_kwh"],
            ),
        )
        for position, item in enumerate(ranked, start=1):
            item["rank"] = position
        return ranked if order == "rank" else items

    def rename_scenario(self, db, scenario_id, data, current_user):
        scenario = self.get_row(db, scenario_id, current_user)[0]
        scenario.name = data.name
        scenario_repository.commit(db)
        return self.get_scenario(db, scenario_id, current_user)

    def delete_scenario(self, db, scenario_id, current_user):
        scenario = self.get_row(db, scenario_id, current_user)[0]
        if scenario_repository.has_decisions(db, scenario_id):
            raise ConflictError(
                "This scenario has recorded decisions so it cannot be deleted"
            )
        scenario_repository.delete(db, scenario)
        scenario_repository.commit(db)


scenario_service = ScenarioService()
