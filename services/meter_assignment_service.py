from datetime import UTC, datetime

from core.exceptions import ConflictError, InvalidDataError, NotFoundError
from core.security import generate_device_token, hash_device_token
from models.enums import DeviceStatus
from models.meter_assignment import MeterAssignment
from repositories.meter_assignment_repository import meter_assignment_repository
from schemas.meter_assignment import MeterAssignmentCreated, MeterAssignmentRead
from services.business_service import business_service
from services.sensor_device_service import sensor_device_service


class MeterAssignmentService:
    def install_meter(self, db, data, current_user):
        device = sensor_device_service.get_device(db, data.device_id, current_user)
        business = business_service.get_business(db, data.business_id, current_user)
        if device.status != DeviceStatus.ACTIVE:
            raise ConflictError("Only active devices can be installed")
        if meter_assignment_repository.get_open_for_device(db, device.device_id):
            raise ConflictError("This device is already installed at a business")
        if meter_assignment_repository.get_open_for_business(db, business.business_id):
            raise ConflictError("This business already has a meter installed")
        token = generate_device_token()
        assignment = MeterAssignment(
            device_id=device.device_id,
            business_id=business.business_id,
            device_token_hash=hash_device_token(token),
            installed_by=current_user.user_id,
        )
        assignment = meter_assignment_repository.create(db, assignment)
        return MeterAssignmentCreated(
            **MeterAssignmentRead.model_validate(assignment).model_dump(),
            device_token=token,
        )

    def remove_meter(self, db, assignment_id, data, current_user):
        assignment = meter_assignment_repository.get_for_organisation(
            db, assignment_id, current_user.organisation_id
        )
        if assignment is None:
            raise NotFoundError("Assignment not found")
        if assignment.removed_at is not None:
            raise ConflictError("This meter has already been removed")
        if not data.buffer_uploaded_confirmed:
            raise InvalidDataError(
                "Confirm the meter has uploaded all buffered readings before removing it"
            )
        assignment.removed_at = datetime.now(UTC)
        return meter_assignment_repository.save(db, assignment)

    def list_assignments(
        self, db, current_user, business_id=None, device_id=None, open_only=False
    ):
        return meter_assignment_repository.list_for_organisation(
            db, current_user.organisation_id, business_id, device_id, open_only
        )


meter_assignment_service = MeterAssignmentService()