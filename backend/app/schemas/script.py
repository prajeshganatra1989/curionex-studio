"""Script workspace API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.scripts.constants import SCRIPT_STATUSES


class ScriptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=20000)
    knowledge_pack_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ScriptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=20000)
    knowledge_pack_id: UUID | None = None
    status: str | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in SCRIPT_STATUSES:
            raise ValueError(
                "status must be one of: " + ", ".join(sorted(SCRIPT_STATUSES))
            )
        return cleaned


class ScriptDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    script_id: UUID
    document_type: str
    title: str
    content: str
    position: int
    created_at: datetime
    updated_at: datetime


class ScriptDocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=500000)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("content must not contain null bytes")
        return value


class ScriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    knowledge_pack_id: UUID | None
    script_code: str
    title: str
    description: str | None
    status: str
    content_version_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    documents: list[ScriptDocumentResponse] = Field(default_factory=list)


class ScriptListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    knowledge_pack_id: UUID | None
    script_code: str
    title: str
    description: str | None
    status: str
    content_version_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ScriptListResponse(BaseModel):
    items: list[ScriptListItem]
    page: int
    page_size: int
    total: int
