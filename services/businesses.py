from collections import defaultdict
from datetime import timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from core.exceptions import ConflictError, NotFoundError
from engine.profiles import build_hourly_profile
from models.business import Business
from models.enums import ConnectionStatus, UserRole
from repositories.businesses import business_repository
from repositories.site_repository import site_repository


class BusinessService:
    def create_business(self, db, data, current_user):
        site = site_repository.get_for_organisation(
            db,
            data.site_id,
            current_user.organisation_id,
        )

        if site is None:
            raise NotFoundError("Site not found")

        if business_repository.get_by_name(db, site.site_id, data.business_name):
            raise ConflictError(
                f"Business '{data.business_name}' already exists at this site."
            )

        business = Business(
            site_id=site.site_id,
            logged_by=current_user.user_id,
            business_name=data.business_name,
            business_type=data.business_type,
            owner_first_name=data.owner_first_name,
            owner_last_name=data.owner_last_name,
            owner_phone=data.owner_phone,
            operating_hours=data.operating_hours,
            days_per_month=data.days_per_month,
            startup_power_kw=data.startup_power_kw,
            startup_duration_s=data.startup_duration_s,
            startup_data_label=data.startup_data_label,
        )

        try:
            return business_repository.create(db, business)
        except IntegrityError:
            db.rollback()
            existing = business_repository.get_by_name(
                db, data.site_id, data.business_name
            )
            if existing:
                raise ConflictError(
                    f"Business '{data.business_name}' already exists at this site."
                )
            raise

    def list_businesses(self, db, current_user):
        return business_repository.list_for_organisation(
            db,
            current_user.organisation_id,
        )

    def get_business(self, db, business_id, current_user):
        business = business_repository.get_for_organisation(
            db,
            business_id,
            current_user.organisation_id,
        )
        if business is None:
            raise NotFoundError("Business not found")
        return business

    def update_business(self, db, business_id, data, current_user):
        business = self.get_business(db, business_id, current_user)

        if current_user.role == UserRole.FIELD_AGENT and (
            business.logged_by != current_user.user_id
            or business.connection_status != ConnectionStatus.PROSPECTIVE
        ):
            raise NotFoundError("Business not found")

        changes = data.model_dump(exclude_unset=True)
        updated_power = changes.get("startup_power_kw", business.startup_power_kw)
        updated_label = changes.get("startup_data_label", business.startup_data_label)

        if (updated_power is None) != (updated_label is None):
            from core.exceptions import AppError

            raise AppError(
                status_code=422,
                detail="Startup power and startup data label must be provided together",
            )

        for field, value in changes.items():
            setattr(business, field, value)

        return business_repository.update(db, business)

    def build_profile(self, db, business, min_days):
        readings = business_repository.readings_for_business(
            db,
            business.business_id,
        )

        lusaka = ZoneInfo("Africa/Lusaka")
        reading_data = []

        for reading in readings:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=lusaka)

            reading_data.append(
                (
                    measured_at,
                    float(reading.power_w),
                    float(reading.energy_total_kwh),
                )
            )

        profile = build_hourly_profile(
            reading_data,
            business.operating_hours,
            lusaka,
        )

        observed_days = profile["observed_days"]

        return {
            **profile,
            "business_id": business.business_id,
            "operating_hours": business.operating_hours,
            "days_per_month": business.days_per_month,
            "startup_power_kw": (
                None
                if business.startup_power_kw is None
                else float(business.startup_power_kw)
            ),
            "startup_duration_s": business.startup_duration_s,
            "startup_data_label": (
                getattr(
                    business.startup_data_label, "value", business.startup_data_label
                )
                if business.startup_data_label is not None
                else None
            ),
            "is_observed": observed_days >= min_days,
        }

    def get_business_profile(self, db, business_id, current_user):
        business = self.get_business(db, business_id, current_user)
        readings = business_repository.readings_for_business(
            db,
            business.business_id,
        )

        lusaka = ZoneInfo("Africa/Lusaka")
        power_totals_w = defaultdict(Decimal)
        power_peaks_w = defaultdict(Decimal)
        reading_counts = defaultdict(int)

        for reading in readings:
            measured_at = reading.measured_at
            if measured_at.tzinfo is None:
                measured_at = measured_at.replace(tzinfo=timezone.utc)
            hour = measured_at.astimezone(lusaka).hour
            power_w = Decimal(str(reading.power_w))
            power_totals_w[hour] += power_w
            power_peaks_w[hour] = max(power_peaks_w[hour], power_w)
            reading_counts[hour] += 1

        hours = []
        for hour in range(24):
            count = reading_counts[hour]
            average_kw = (
                round(
                    float(power_totals_w[hour] / count / Decimal("1000")),
                    3,
                )
                if count
                else None
            )
            peak_kw = (
                round(float(power_peaks_w[hour] / Decimal("1000")), 3)
                if count
                else None
            )
            hours.append(
                {
                    "hour": hour,
                    "average_power_kw": average_kw,
                    "peak_power_kw": peak_kw,
                    "reading_count": count,
                }
            )

        return {"business_id": business.business_id, "hours": hours}


business_service = BusinessService()
