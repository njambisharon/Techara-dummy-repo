from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganisationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organisation_id: UUID
    organisation_name: str = Field(max_length=100)
    created_at: datetime


class OrganisationUpdate(BaseModel):
    organisation_name: str = Field(min_length=1, max_length=100)
