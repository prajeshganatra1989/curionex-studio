"""Content production workflow API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.workflows.constants import WORKFLOW_STAGES


class WorkflowScriptSummary(BaseModel):
    id: UUID
    script_code: str
    title: str
    status: str
    knowledge_pack_id: UUID | None
    project_id: UUID


class WorkflowVersionSummary(BaseModel):
    id: UUID
    version_number: int
    status: str
    title: str
    created_at: datetime


class WorkflowApprovalSummary(BaseModel):
    id: UUID
    status: str
    content_version_id: UUID
    created_at: datetime
    reviewed_at: datetime | None


class ContentWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    script_id: UUID
    current_stage: str
    status: str
    active_content_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    script: WorkflowScriptSummary | None = None
    knowledge_pack_id: UUID | None = None
    active_content_version: WorkflowVersionSummary | None = None
    latest_approval: WorkflowApprovalSummary | None = None


class WorkflowVersionRef(BaseModel):
    id: UUID
    version_number: int
    status: str
    title: str


class WorkflowStatusResponse(BaseModel):
    script_id: UUID
    stage: str
    status: str
    active_version: WorkflowVersionRef | None = None
    latest_version: WorkflowVersionRef | None = None
    approved_version: WorkflowVersionRef | None = None
    pending_approval: WorkflowApprovalSummary | None = None


class WorkflowTransitionRequest(BaseModel):
    target_stage: str = Field(min_length=1, max_length=32)

    @field_validator("target_stage")
    @classmethod
    def validate_target_stage(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in WORKFLOW_STAGES:
            raise ValueError(
                "target_stage must be one of: " + ", ".join(sorted(WORKFLOW_STAGES))
            )
        return cleaned


class WorkflowVersionCreateResponse(BaseModel):
    workflow: ContentWorkflowResponse
    content_version: WorkflowVersionSummary


class WorkflowReviewResponse(BaseModel):
    workflow: ContentWorkflowResponse
    approval: WorkflowApprovalSummary
    content_version: WorkflowVersionSummary
