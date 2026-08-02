"""Editorial Library API schemas."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.editorial.constants import (
    DEFAULT_TOPIC_DIFFICULTY,
    DEFAULT_TOPIC_STATUS,
    DEFAULT_TOPIC_VIRAL,
    TOPIC_DIFFICULTIES,
    TOPIC_STATUSES,
    TOPIC_VIRAL_POTENTIALS,
)
from app.schemas.project import ProjectResponse, normalize_slug

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_title_key(title: str) -> str:
    """Normalize a title for duplicate detection (lowercase alphanumeric words)."""
    lowered = title.strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


class EditorialTopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    slug: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=10000)
    category: str = Field(min_length=1, max_length=80)
    status: str = DEFAULT_TOPIC_STATUS
    difficulty: str = DEFAULT_TOPIC_DIFFICULTY
    evergreen_score: int = Field(default=70, ge=0, le=100)
    curiosity_score: int = Field(default=70, ge=0, le=100)
    viral_potential: str = DEFAULT_TOPIC_VIRAL
    estimated_duration_seconds: int = Field(default=45, ge=15, le=180)
    target_audience: str | None = Field(default=None, max_length=200)
    source: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)
    is_featured: bool = False
    published_video_url: str | None = Field(default=None, max_length=500)

    @field_validator("title", "category")
    @classmethod
    def strip_required(cls, value: str) -> str:
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

    @field_validator(
        "description",
        "target_audience",
        "source",
        "notes",
        "published_video_url",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in TOPIC_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(TOPIC_STATUSES))}")
        return value

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value: str) -> str:
        if value not in TOPIC_DIFFICULTIES:
            raise ValueError(
                f"difficulty must be one of: {', '.join(sorted(TOPIC_DIFFICULTIES))}"
            )
        return value

    @field_validator("viral_potential")
    @classmethod
    def validate_viral(cls, value: str) -> str:
        if value not in TOPIC_VIRAL_POTENTIALS:
            raise ValueError(
                "viral_potential must be one of: "
                f"{', '.join(sorted(TOPIC_VIRAL_POTENTIALS))}"
            )
        return value


class EditorialTopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    slug: str | None = Field(default=None, max_length=180)
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    status: str | None = None
    difficulty: str | None = None
    evergreen_score: int | None = Field(default=None, ge=0, le=100)
    curiosity_score: int | None = Field(default=None, ge=0, le=100)
    viral_potential: str | None = None
    estimated_duration_seconds: int | None = Field(default=None, ge=15, le=180)
    target_audience: str | None = Field(default=None, max_length=200)
    source: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)
    is_featured: bool | None = None
    published_video_url: str | None = Field(default=None, max_length=500)

    @field_validator("title", "category")
    @classmethod
    def strip_required_optional(cls, value: str | None) -> str | None:
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

    @field_validator(
        "description",
        "target_audience",
        "source",
        "notes",
        "published_video_url",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in TOPIC_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(TOPIC_STATUSES))}")
        return value

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in TOPIC_DIFFICULTIES:
            raise ValueError(
                f"difficulty must be one of: {', '.join(sorted(TOPIC_DIFFICULTIES))}"
            )
        return value

    @field_validator("viral_potential")
    @classmethod
    def validate_viral(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in TOPIC_VIRAL_POTENTIALS:
            raise ValueError(
                "viral_potential must be one of: "
                f"{', '.join(sorted(TOPIC_VIRAL_POTENTIALS))}"
            )
        return value


class LinkedProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_code: str
    name: str
    status: str


class EditorialTopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str | None
    category: str
    status: str
    difficulty: str
    evergreen_score: int
    curiosity_score: int
    viral_potential: str
    estimated_duration_seconds: int
    target_audience: str | None
    source: str | None
    notes: str | None
    linked_project_id: UUID | None
    published_video_url: str | None
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    linked_project: LinkedProjectSummary | None = None


class EditorialTopicListResponse(BaseModel):
    items: list[EditorialTopicResponse]
    page: int
    page_size: int
    total: int


class DuplicateTitleWarning(BaseModel):
    similar_topic_id: UUID
    similar_title: str
    similar_slug: str


class EditorialTopicCreateResponse(BaseModel):
    topic: EditorialTopicResponse
    duplicate_warning: DuplicateTitleWarning | None = None


class CreateProjectFromTopicRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    category_id: UUID | None = None
    tag_ids: list[UUID] = Field(default_factory=list)

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

    @model_validator(mode="after")
    def unique_tags(self) -> CreateProjectFromTopicRequest:
        if len(self.tag_ids) != len(set(self.tag_ids)):
            raise ValueError("tag_ids must be unique")
        return self


class CreateProjectFromTopicResponse(BaseModel):
    topic: EditorialTopicResponse
    project: ProjectResponse


class EditorialTopicSummaryResponse(BaseModel):
    available: int
    in_progress: int
    published: int
    project_created: int
    total_active: int
