import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SiteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    site_name: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)


class SiteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    site_name: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, min_length=1, max_length=100)


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    site_id: uuid.UUID
    organisation_id: uuid.UUID
    site_name: str
    district: str
    created_by: uuid.UUID
    created_at: datetime
