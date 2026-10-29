import uuid
from typing import Literal

from core.dependencies import require_roles
from core.roles import OPERATOR_ONLY
from database import get_db
from fastapi import APIRouter, Depends, Query, status
from models.user import User
from schemas.scenario import (
    CompareSitesCreate,
    ScenarioCreate,
    ScenarioRead,
    ScenarioSummary,
    ScenarioUpdate,
)
from services.scenario_service import scenario_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def run_scenario(
    data: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return scenario_service.create_scenario(db, data, current_user)


@router.post(
    "/compare-sites",
    response_model=list[ScenarioSummary],
    status_code=status.HTTP_201_CREATED,
)
def compare_sites(
    data: CompareSitesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return scenario_service.compare_sites(db, data, current_user)


@router.get("", response_model=list[ScenarioSummary])
def list_scenarios(
    site_id: uuid.UUID | None = None,
    profile_id: uuid.UUID | None = None,
    business_id: uuid.UUID | None = None,
    scenario_ids: list[uuid.UUID] | None = Query(default=None),
    order: Literal["rank", "newest"] = "rank",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return scenario_service.list_scenarios(
        db, current_user, site_id, profile_id, business_id, scenario_ids, order
    )


@router.get("/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return scenario_service.get_scenario(db, scenario_id, current_user)


@router.patch("/{scenario_id}", response_model=ScenarioRead)
def rename_scenario(
    scenario_id: uuid.UUID,
    data: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    return scenario_service.rename_scenario(db, scenario_id, data, current_user)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*OPERATOR_ONLY)),
):
    scenario_service.delete_scenario(db, scenario_id, current_user)
