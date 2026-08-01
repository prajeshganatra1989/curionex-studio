"""RBAC API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.rbac_service import normalize_role_name


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = normalize_role_name(value)
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    detail: str
