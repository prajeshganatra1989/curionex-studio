"""Knowledge Pack API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.knowledge_packs.constants import (
    DEFAULT_KNOWLEDGE_PACK_STATUS,
    KNOWLEDGE_PACK_STATUSES,
)


class KnowledgePackCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    status: str = DEFAULT_KNOWLEDGE_PACK_STATUS

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
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
    def validate_status(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in KNOWLEDGE_PACK_STATUSES:
            raise ValueError(
                "status must be one of: "
                + ", ".join(sorted(KNOWLEDGE_PACK_STATUSES))
            )
        return cleaned


class KnowledgePackUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    status: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
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
        if cleaned not in KNOWLEDGE_PACK_STATUSES:
            raise ValueError(
                "status must be one of: "
                + ", ".join(sorted(KNOWLEDGE_PACK_STATUSES))
            )
        return cleaned


class KnowledgePackSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_pack_id: UUID
    section_key: str
    title: str
    content: str
    position: int
    created_at: datetime
    updated_at: datetime


class KnowledgePackSectionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=200000)

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
    def normalize_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # Plain text — preserve intentional whitespace but reject null bytes.
        if "\x00" in value:
            raise ValueError("content must not contain null bytes")
        return value


class KnowledgePackReorderRequest(BaseModel):
    """Documented shape when callers wrap keys; routes accept a bare list."""

    section_keys: list[str] = Field(min_length=1)

    @field_validator("section_keys")
    @classmethod
    def validate_keys(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("section keys must not be empty")
        return cleaned


class KnowledgePackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    sections: list[KnowledgePackSectionResponse] = Field(default_factory=list)


class KnowledgePackListItem(BaseModel):
    """List item without nested sections (avoids heavy payloads)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class KnowledgePackListResponse(BaseModel):
    items: list[KnowledgePackListItem]
    page: int
    page_size: int
    total: int
