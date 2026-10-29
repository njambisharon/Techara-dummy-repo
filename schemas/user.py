from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

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

    @model_validator(mode="after")
    def validate_updates(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")

        for field in ("first_name", "last_name", "email", "phone_number"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")

        return self


class CreateUserRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_fields(self):
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()

        if not self.first_name:
            raise ValueError("first_name cannot be empty")
        if not self.last_name:
            raise ValueError("last_name cannot be empty")

        if self.role == UserRole.FIELD_AGENT:
            if not self.phone_number or not self.phone_number.strip():
                raise ValueError("phone_number is required for field agents")
            self.phone_number = self.phone_number.strip()

        elif self.role == UserRole.OPERATOR:
            if not self.email:
                raise ValueError("email is required for operators")
            self.email = str(self.email).strip().lower()

        else:
            raise ValueError("This role cannot be created through this endpoint")

        return self


class CreateUserResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class CreateFieldAgentRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_fields(self):
        for field in ("first_name", "last_name", "phone_number"):
            value = getattr(self, field).strip()
            if not value:
                raise ValueError(f"{field} cannot be empty")
            setattr(self, field, value)
        return self


class CreateFieldAgentResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class CreateOperatorRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @model_validator(mode="after")
    def validate_fields(self):
        self.first_name = self.first_name.strip()
        self.last_name = self.last_name.strip()

        if not self.first_name:
            raise ValueError("first_name cannot be empty")
        if not self.last_name:
            raise ValueError("last_name cannot be empty")

        self.email = str(self.email).strip().lower()
        return self


class CreateOperatorResponse(BaseModel):
    user: UserProfileResponse
    temporary_password: str
    message: str


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class UpdateUserStatusResponse(BaseModel):
    message: str
    user: UserProfileResponse
