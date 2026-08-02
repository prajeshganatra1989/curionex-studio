"""Content Standard API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.editorial.content_standard_constants import (
    CONTENT_STANDARD_STATUS_DRAFT,
    CONTENT_STANDARD_STATUSES,
)


class ContentStandardBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=40)
    mission: str = Field(min_length=1, max_length=20000)
    target_audience: str = Field(min_length=1, max_length=20000)
    brand_voice: str = Field(min_length=1, max_length=20000)
    editorial_principles: str = Field(min_length=1, max_length=20000)
    hook_rules: str = Field(min_length=1, max_length=20000)
    story_structure: str = Field(min_length=1, max_length=20000)
    fact_policy: str = Field(min_length=1, max_length=20000)
    citation_policy: str = Field(min_length=1, max_length=20000)
    tone_guidelines: str = Field(min_length=1, max_length=20000)
    language_rules: str = Field(min_length=1, max_length=20000)
    forbidden_patterns: str = Field(min_length=1, max_length=20000)
    approved_cta_patterns: str = Field(min_length=1, max_length=20000)
    quality_checklist: str = Field(min_length=1, max_length=20000)
    default_duration_seconds: int = Field(default=60, ge=15, le=600)
    default_target_words: int = Field(default=160, ge=20, le=2000)
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator(
        "name",
        "version",
        "mission",
        "target_audience",
        "brand_voice",
        "editorial_principles",
        "hook_rules",
        "story_structure",
        "fact_policy",
        "citation_policy",
        "tone_guidelines",
        "language_rules",
        "forbidden_patterns",
        "approved_cta_patterns",
        "quality_checklist",
    )
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ContentStandardCreate(ContentStandardBase):
    status: str = CONTENT_STANDARD_STATUS_DRAFT

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in CONTENT_STANDARD_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(CONTENT_STANDARD_STATUSES))}"
            )
        return value


class ContentStandardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    version: str | None = Field(default=None, min_length=1, max_length=40)
    mission: str | None = Field(default=None, min_length=1, max_length=20000)
    target_audience: str | None = Field(default=None, min_length=1, max_length=20000)
    brand_voice: str | None = Field(default=None, min_length=1, max_length=20000)
    editorial_principles: str | None = Field(
        default=None, min_length=1, max_length=20000
    )
    hook_rules: str | None = Field(default=None, min_length=1, max_length=20000)
    story_structure: str | None = Field(default=None, min_length=1, max_length=20000)
    fact_policy: str | None = Field(default=None, min_length=1, max_length=20000)
    citation_policy: str | None = Field(default=None, min_length=1, max_length=20000)
    tone_guidelines: str | None = Field(default=None, min_length=1, max_length=20000)
    language_rules: str | None = Field(default=None, min_length=1, max_length=20000)
    forbidden_patterns: str | None = Field(default=None, min_length=1, max_length=20000)
    approved_cta_patterns: str | None = Field(
        default=None, min_length=1, max_length=20000
    )
    quality_checklist: str | None = Field(default=None, min_length=1, max_length=20000)
    default_duration_seconds: int | None = Field(default=None, ge=15, le=600)
    default_target_words: int | None = Field(default=None, ge=20, le=2000)
    notes: str | None = Field(default=None, max_length=20000)

    @field_validator(
        "name",
        "version",
        "mission",
        "target_audience",
        "brand_voice",
        "editorial_principles",
        "hook_rules",
        "story_structure",
        "fact_policy",
        "citation_policy",
        "tone_guidelines",
        "language_rules",
        "forbidden_patterns",
        "approved_cta_patterns",
        "quality_checklist",
    )
    @classmethod
    def strip_optional_required(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ContentStandardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    version: str
    status: str
    mission: str
    target_audience: str
    brand_voice: str
    editorial_principles: str
    hook_rules: str
    story_structure: str
    fact_policy: str
    citation_policy: str
    tone_guidelines: str
    language_rules: str
    forbidden_patterns: str
    approved_cta_patterns: str
    quality_checklist: str
    default_duration_seconds: int
    default_target_words: int
    notes: str | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class ContentStandardListResponse(BaseModel):
    items: list[ContentStandardResponse]
    total: int


class ContentStandardSummaryResponse(BaseModel):
    """Compact active-standard summary for Settings and prompt badges."""

    id: UUID | None = None
    name: str | None = None
    version: str | None = None
    status: str | None = None
    label: str | None = None
    updated_at: datetime | None = None
    has_active: bool = False
