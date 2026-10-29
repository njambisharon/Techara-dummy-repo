
from core.exceptions import NotFoundError
from models.business import Business
from repositories.business_repository import business_repository
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
        )

        return business_repository.create(db, business)

    def list_businesses(self, db, current_user):
        return business_repository.list_for_organisation(
            db,
            current_user.organisation_id,
        )

    def get_business(self, db, business_id, current_user):
        business = business_repository.get_for_organisation(
            db, business_id, current_user.organisation_id
        )
        if business is None:
            raise NotFoundError("Business not found")
        return business

    def update_business(self, db, business_id, data, current_user):
        business = self.get_business(db, business_id, current_user)
        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(business, field, value)

        return business_repository.update(db, business)


    def get_business_profile(self, db, business_id, current_user):
        from collections import defaultdict
        from decimal import Decimal

        # Reuse the organisation-scoped lookup to avoid leaking another
        # organisation's business or meter data.
        business = self.get_business(db, business_id, current_user)
        readings = business_repository.readings_for_business(db, business.business_id)

        power_totals_w = defaultdict(Decimal)
        reading_counts = defaultdict(int)

        for reading in readings:
            hour = reading.measured_at.hour
            power_totals_w[hour] += Decimal(str(reading.power_w))
            reading_counts[hour] += 1

        hours = []
        for hour in range(24):
            count = reading_counts[hour]
            average_kw = (
                round(float(power_totals_w[hour] / count / Decimal("1000")), 3)
                if count
                else None
            )
            hours.append(
                {
                    "hour": hour,
                    "average_power_kw": average_kw,
                    "reading_count": count,
                }
            )

        return {"business_id": business.business_id, "hours": hours}


business_service = BusinessService()
