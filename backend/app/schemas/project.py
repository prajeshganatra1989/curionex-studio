"""Project, category, and tag API schemas."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.projects.constants import DEFAULT_PROJECT_STATUS, PROJECT_STATUSES

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_slug(value: str) -> str:
    """Normalize a taxonomy slug to lowercase kebab-case."""
    cleaned = value.strip().lower().replace("_", "-")
    cleaned = re.sub(r"[^a-z0-9-]+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = Field(default=None, max_length=5000)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("slug")
    @classmethod
    def normalize_optional_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalize_slug(value)
        if not cleaned or not _SLUG_RE.match(cleaned):
            raise ValueError("slug must be lowercase kebab-case")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)
    description: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("slug")
    @classmethod
    def normalize_optional_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalize_slug(value)
        if not cleaned or not _SLUG_RE.match(cleaned):
            raise ValueError("slug must be lowercase kebab-case")
        return cleaned

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("slug")
    @classmethod
    def normalize_optional_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalize_slug(value)
        if not cleaned or not _SLUG_RE.match(cleaned):
            raise ValueError("slug must be lowercase kebab-case")
        return cleaned


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=140)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("slug")
    @classmethod
    def normalize_optional_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = normalize_slug(value)
        if not cleaned or not _SLUG_RE.match(cleaned):
            raise ValueError("slug must be lowercase kebab-case")
        return cleaned


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    status: str = DEFAULT_PROJECT_STATUS
    category_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)

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
        if cleaned not in PROJECT_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(PROJECT_STATUSES))}"
            )
        return cleaned

    @field_validator("tag_ids")
    @classmethod
    def dedupe_tag_ids(cls, value: list[UUID]) -> list[UUID]:
        seen: set[UUID] = set()
        result: list[UUID] = []
        for tag_id in value:
            if tag_id not in seen:
                seen.add(tag_id)
                result.append(tag_id)
        return result


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None

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
        if cleaned not in PROJECT_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(PROJECT_STATUSES))}"
            )
        return cleaned

    @field_validator("tag_ids")
    @classmethod
    def dedupe_tag_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None
        seen: set[UUID] = set()
        result: list[UUID] = []
        for tag_id in value:
            if tag_id not in seen:
                seen.add(tag_id)
                result.append(tag_id)
        return result


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    email: str
    first_name: str
    last_name: str
    created_at: datetime


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_code: str
    name: str
    description: str | None
    status: str
    category_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse | None = None
    tags: list[TagResponse] = Field(default_factory=list)


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    page: int
    page_size: int
    total: int


class MessageResponse(BaseModel):
    detail: str
