import uuid
from datetime import UTC, datetime

from core.security import generate_device_token, hash_device_token
from fastapi import HTTPException
from models.enums import DeviceStatus
from models.meter_assignment import MeterAssignment
from repositories.meter_assignment_repository import meter_assignment_repository
from schemas.meter_assignment import (
    MeterAssignmentCreate,
    MeterAssignmentCreated,
    MeterAssignmentRead,
)
from sqlalchemy.exc import IntegrityError


class MeterAssignmentService:
    def install_meter(self, db, data: MeterAssignmentCreate, current_user):
        device = meter_assignment_repository.get_device_for_organisation(
            db,
            data.device_id,
            current_user.organisation_id,
        )
        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")

        business = meter_assignment_repository.get_business_for_organisation(
            db,
            data.business_id,
            current_user.organisation_id,
        )
        if business is None:
            raise HTTPException(status_code=404, detail="Business not found")

        if device.status != DeviceStatus.ACTIVE:
            raise HTTPException(
                status_code=409,
                detail="Only active devices can be installed",
            )

        if meter_assignment_repository.get_open_for_device(db, device.device_id):
            raise HTTPException(
                status_code=409,
                detail="This device is already installed at a business",
            )

        if meter_assignment_repository.get_open_for_business(db, business.business_id):
            raise HTTPException(
                status_code=409,
                detail="This business already has a meter installed",
            )

        token = generate_device_token()
        assignment = MeterAssignment(
            device_id=device.device_id,
            business_id=business.business_id,
            device_token_hash=hash_device_token(token),
            installed_by=current_user.user_id,
        )

        try:
            assignment = meter_assignment_repository.create(db, assignment)
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Device or business already has an open meter installed",
            )

        return MeterAssignmentCreated(
            **MeterAssignmentRead.model_validate(assignment).model_dump(),
            device_token=token,
        )

    def get_assignment(self, db, current_user, assignment_id: uuid.UUID):
        assignment = meter_assignment_repository.get_for_organisation(
            db,
            assignment_id,
            current_user.organisation_id,
        )

        if assignment is None:
            raise HTTPException(status_code=404, detail="Assignment not found")

        return assignment

    def remove_meter(self, db, assignment_id: uuid.UUID, current_user):
        assignment = self.get_assignment(db, current_user, assignment_id)

        if assignment.removed_at is not None:
            raise HTTPException(
                status_code=409,
                detail="This meter has already been removed",
            )

        assignment.removed_at = datetime.now(UTC)

        return meter_assignment_repository.save(db, assignment)

    def list_assignments(
        self,
        db,
        current_user,
        business_id=None,
        device_id=None,
        open_only=False,
    ):
        return meter_assignment_repository.list_for_organisation(
            db,
            current_user.organisation_id,
            business_id,
            device_id,
            open_only,
        )


meter_assignment_service = MeterAssignmentService()
