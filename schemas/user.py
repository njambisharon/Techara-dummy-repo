from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from models.enums import UserRole


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    organisation_id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone_number: str | None
    role: UserRole
    is_active: bool
    must_change_password: bool
    created_at: datetime


class UserProfileUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=1, max_length=20)


class CreateUserRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=1, max_length=20)


class CreateUserResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class CreateFieldAgentRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(min_length=1, max_length=20)


class CreateFieldAgentResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class CreateOperatorRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class CreateOperatorResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class UpdateUserStatusResponse(BaseModel):
    message: str
    user: UserProfileResponse
