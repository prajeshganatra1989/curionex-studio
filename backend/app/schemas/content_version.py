"""Content version and approval API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ContentVersionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=0, max_length=500000)
    script_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("content must not contain null bytes")
        return value


class ContentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    script_id: UUID | None = None
    version_number: int
    status: str
    title: str
    content: str
    created_by: UUID
    created_at: datetime


class ContentVersionListResponse(BaseModel):
    items: list[ContentVersionResponse]
    page: int
    page_size: int
    total: int


class ContentVersionSummary(BaseModel):
    """Version row without full snapshot content (list/inbox)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    script_id: UUID | None = None
    version_number: int
    status: str
    title: str
    created_by: UUID
    created_at: datetime


class ApprovalRequestCreate(BaseModel):
    comment: str | None = Field(default=None, max_length=5000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ApprovalReviewRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=5000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content_version_id: UUID
    requested_by: UUID
    reviewed_by: UUID | None
    status: str
    comment: str | None
    created_at: datetime
    reviewed_at: datetime | None


class UserBrief(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str


class ProjectBrief(BaseModel):
    id: UUID
    project_code: str
    name: str


class ScriptBrief(BaseModel):
    id: UUID
    script_code: str
    title: str
    project_id: UUID
    knowledge_pack_id: UUID | None = None


class ApprovalListItem(BaseModel):
    id: UUID
    status: str
    comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    requested_by: UserBrief
    reviewed_by: UserBrief | None
    content_version: ContentVersionSummary
    project: ProjectBrief
    script: ScriptBrief | None = None


class ApprovalListResponse(BaseModel):
    items: list[ApprovalListItem]
    page: int
    page_size: int
    total: int


class ApprovalDetailResponse(BaseModel):
    id: UUID
    status: str
    comment: str | None
    created_at: datetime
    reviewed_at: datetime | None
    requested_by: UserBrief
    reviewed_by: UserBrief | None
    content_version: ContentVersionResponse
    project: ProjectBrief
    script: ScriptBrief | None = None
    version_approvals: list[ApprovalResponse] = Field(default_factory=list)
