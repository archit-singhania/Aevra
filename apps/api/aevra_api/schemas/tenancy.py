import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    # Temporary staging policy: production must restore a stronger minimum
    # before public registration is enabled.
    password: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    organization_name: str = Field(min_length=2, max_length=160)
    workspace_name: str = Field(min_length=2, max_length=160)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.count("@") != 1 or "." not in normalized.rsplit("@", 1)[1]:
            raise ValueError("Enter a valid email address")
        return normalized


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    is_active: bool
    created_at: datetime


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    timezone: str
    is_active: bool
    created_at: datetime


class RegistrationResponse(BaseModel):
    user: UserResponse
    organization: OrganizationResponse
    workspace: WorkspaceResponse
    token: TokenResponse


class AccountDeletionResponse(BaseModel):
    request_id: uuid.UUID
    status: str
    requested_at: datetime
    scheduled_for: datetime


class AccountDeletionCreateRequest(BaseModel):
    confirmation_email: str = Field(min_length=3, max_length=320)


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
