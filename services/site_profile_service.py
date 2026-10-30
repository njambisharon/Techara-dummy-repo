import csv
import io
import math
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.defaults import SITE_TIMEZONE, SUGGESTED_SETTINGS
from core.exceptions import ConflictError, InvalidDataError, NotFoundError
from engine.site_data import average_monitoring_export
from engine.spare_capacity import spare_capacity
from models.site_profile import SiteProfile
from repositories.site_profile_repository import site_profile_repository
from services.site_service import site_service
from sqlalchemy.exc import IntegrityError

TIME_COLUMNS = ("timestamp", "time", "datetime", "date_time")
LOAD_COLUMNS = ("load_kw", "demand_kw", "consumption_kw")
SOLAR_COLUMNS = ("solar_kw", "pv_kw", "generation_kw")


def pick_column(headers, options):
    for option in options:
        if option in headers:
            return headers[option]
    return None


def find_column(headers, name):
    column = headers.get(name.strip().lower())
    if column is None:
        raise InvalidDataError(f"Column '{name}' was not found in the CSV")
    return column


def describe_row(row):
    return ",".join(str(value) for value in row.values())[:100]


def read_monitoring_rows(csv_text, column_map=None):
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    headers = {name.strip().lower(): name for name in reader.fieldnames or []}
    if column_map is not None:
        time_column = find_column(headers, column_map.timestamp)
        load_column = find_column(headers, column_map.load_kw)
        solar_column = find_column(headers, column_map.solar_kw)
    else:
        time_column = pick_column(headers, TIME_COLUMNS)
        load_column = pick_column(headers, LOAD_COLUMNS)
        solar_column = pick_column(headers, SOLAR_COLUMNS)
        if not time_column or not load_column or not solar_column:
            raise InvalidDataError(
                "The CSV needs timestamp, load_kw and solar_kw columns"
            )
    rows = []
    skipped = 0
    first_skipped = None
    for row in reader:
        try:
            timestamp = datetime.fromisoformat(row[time_column].strip())
            load_kw = float(row[load_column])
            solar_kw = float(row[solar_column])
        except (TypeError, ValueError, AttributeError):
            skipped += 1
            first_skipped = first_skipped or describe_row(row)
            continue
        if not (math.isfinite(load_kw) and math.isfinite(solar_kw)):
            skipped += 1
            first_skipped = first_skipped or describe_row(row)
            continue
        if load_kw < 0 or solar_kw < 0:
            skipped += 1
            first_skipped = first_skipped or describe_row(row)
            continue
        rows.append((timestamp, load_kw, solar_kw))
    return rows, skipped, first_skipped


def to_float(value):
    return None if value is None else float(value)


def to_engine_site(profile):
    return {
        "inverter_continuous_kw": to_float(profile.inverter_continuous_kw),
        "inverter_surge_kw": to_float(profile.inverter_surge_kw),
        "inverter_surge_duration_s": profile.inverter_surge_duration_s,
        "battery_nominal_kwh": float(profile.battery_nominal_kwh),
        "soc_min_percent": float(profile.soc_min_percent),
        "soc_max_percent": float(profile.soc_max_percent),
        "charge_efficiency": float(profile.charge_efficiency),
        "discharge_efficiency": float(profile.discharge_efficiency),
        "max_charge_kw": float(profile.max_charge_kw),
        "max_discharge_kw": float(profile.max_discharge_kw),
        "tariff_per_kwh": float(profile.tariff_per_kwh),
        "baseline_demand_kw": [float(value) for value in profile.baseline_demand_kw],
        "solar_profile": {
            "average_kw": [
                float(value) for value in profile.solar_profile["average_kw"]
            ],
            "low_sun_kw": [
                float(value) for value in profile.solar_profile["low_sun_kw"]
            ],
        },
        "settings": {**SUGGESTED_SETTINGS, **profile.settings},
        "data_labels": profile.data_labels,
    }


class SiteProfileService:
    def create_profile(self, db, site_id, data, current_user):
        site = site_service.get_site(db, site_id, current_user)
        values = data.model_dump()
        values["settings"] = data.settings.model_dump()
        values["data_labels"] = data.data_labels.model_dump(mode="json")
        profile = SiteProfile(
            site_id=site.site_id,
            version=site_profile_repository.next_version(db, site.site_id),
            created_by=current_user.user_id,
            **values,
        )
        try:
            return site_profile_repository.create(db, profile)
        except IntegrityError as error:
            db.rollback()
            detail = str(error.orig)
            if (
                "uq_site_profile_site_version" in detail
                or "site_profile.version" in detail
            ):
                raise ConflictError(
                    "Another profile version was saved at the same time, try again"
                )
            raise

    def list_profiles(self, db, site_id, current_user):
        site = site_service.get_site(db, site_id, current_user)
        return site_profile_repository.list_for_site(db, site.site_id)

    def get_latest_profile(self, db, site_id, current_user):
        site = site_service.get_site(db, site_id, current_user)
        profile = site_profile_repository.latest_for_site(db, site.site_id)
        if profile is None:
            raise NotFoundError("This site has no profile yet")
        return profile

    def import_monitoring_export(self, db, site_id, data, current_user):
        site_service.get_site(db, site_id, current_user)
        try:
            source_timezone = ZoneInfo(data.source_timezone)
        except (ZoneInfoNotFoundError, ValueError):
            raise InvalidDataError("Unknown source timezone")
        rows, skipped, first_skipped = read_monitoring_rows(
            data.csv_text, data.column_map
        )
        if not rows:
            raise InvalidDataError(
                "No usable rows found in the CSV. Timestamps must look like "
                f"2026-10-01T13:00:00. First skipped row: {first_skipped}"
            )
        try:
            result = average_monitoring_export(rows, SITE_TIMEZONE, source_timezone)
        except ValueError as error:
            raise InvalidDataError(str(error))
        min_days = SUGGESTED_SETTINGS["min_observed_days"]
        data_label = "observed" if result["complete_days"] >= min_days else "estimated"
        return {
            **result,
            "suggested_settings": SUGGESTED_SETTINGS,
            "suggested_data_labels": {
                "baseline": data_label,
                "solar": data_label,
                "battery": "user_entered",
            },
            "rows_read": len(rows),
            "rows_skipped": skipped,
        }

    def get_spare_capacity(self, db, site_id, current_user):
        profile = self.get_latest_profile(db, site_id, current_user)
        return {
            "site_id": profile.site_id,
            "profile_id": profile.profile_id,
            "profile_version": profile.version,
            **spare_capacity(to_engine_site(profile)),
        }


site_profile_service = SiteProfileService()
