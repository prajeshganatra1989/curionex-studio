"""Audit API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    created_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="event_metadata",
        serialization_alias="metadata",
    )

    @field_validator("ip_address", mode="before")
    @classmethod
    def coerce_ip_address(cls, value: object) -> str | None:
        if value is None:
            return None
        return str(value)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    page: int
    page_size: int
    total: int
