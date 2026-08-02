"""Production Mode API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.production.stages import (
    MAX_APPROVED_TARGET,
    MAX_DAILY_TARGET,
    MAX_WEEKLY_TARGET,
    PRODUCTION_STAGES,
)

ProductionStageLiteral = Literal[
    "idea",
    "research",
    "discovery_brief",
    "story_spine",
    "master_script",
    "quality_review",
    "needs_revision",
    "ready_for_version",
    "version_created",
    "pending_human_review",
    "approved",
    "blocked",
    "archived",
]

DocumentStatusLiteral = Literal["complete", "incomplete", "missing"]

MetricsRangeLiteral = Literal["today", "7d", "30d"]

QualityBandLiteral = Literal[
    "excellent",
    "strong",
    "needs_refinement",
    "weak",
    "major_revision_required",
]


class ProductionSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    approved_script_target: int
    daily_approved_script_target: int
    weekly_approved_script_target: int
    updated_at: datetime
    updated_by: UUID | None = None


class ProductionSettingsUpdate(BaseModel):
    approved_script_target: int | None = Field(
        default=None, ge=1, le=MAX_APPROVED_TARGET
    )
    daily_approved_script_target: int | None = Field(
        default=None, ge=1, le=MAX_DAILY_TARGET
    )
    weekly_approved_script_target: int | None = Field(
        default=None, ge=1, le=MAX_WEEKLY_TARGET
    )


class ProductionNextAction(BaseModel):
    code: str
    label: str
    href: str | None = None
    reason: str
    blocked: bool = False


class ProductionGoalsSummary(BaseModel):
    approved_target: int
    approved_total: int
    remaining: int
    completion_percent: float
    daily_target: int
    approved_today: int
    weekly_target: int
    approved_this_week: int
    projected_days_remaining: float | None = None


class ProductionAiSummary(BaseModel):
    queued: int
    running: int
    failed: int
    completed_today: int
    estimated_cost_today: float
    estimated_cost_this_week: float


class ProductionQualitySummary(BaseModel):
    average_current_score: float | None = None
    scripts_needing_revision: int
    stale_reviews: int
    high_risk_fact_flags: int


class ProductionCatalogSummary(BaseModel):
    """Membership-scoped entity totals for Dashboard / overview cards."""

    projects: int
    knowledge_packs: int
    scripts: int
    draft_scripts: int


class ProductionOverviewResponse(BaseModel):
    goals: ProductionGoalsSummary
    stage_counts: dict[str, int]
    ai: ProductionAiSummary
    quality: ProductionQualitySummary
    catalog: ProductionCatalogSummary


class ProductionDocumentStatuses(BaseModel):
    discovery_brief: DocumentStatusLiteral
    story_spine: DocumentStatusLiteral
    master_script: DocumentStatusLiteral


class ProductionQualityItem(BaseModel):
    score: int | None = None
    band: str | None = None
    stale: bool = False
    recommendation: str | None = None
    generation_id: UUID | None = None
    high_risk_facts: int = 0


class ProductionWorkflowItem(BaseModel):
    stage: str | None = None
    status: str | None = None
    active_version_id: UUID | None = None


class ProductionApprovalItem(BaseModel):
    status: str | None = None
    approval_id: UUID | None = None


class ProductionAiJobItem(BaseModel):
    status: str | None = None
    job_id: UUID | None = None
    purpose: str | None = None
    error_message: str | None = None


class ProductionQueueItem(BaseModel):
    script_id: UUID | None = None
    project_id: UUID
    project_code: str
    project_name: str
    script_code: str | None = None
    script_title: str | None = None
    script_status: str | None = None
    production_stage: ProductionStageLiteral
    next_action: ProductionNextAction
    knowledge_pack_id: UUID | None = None
    knowledge_pack_completion: int = 0
    documents: ProductionDocumentStatuses
    quality: ProductionQualityItem
    workflow: ProductionWorkflowItem
    approval: ProductionApprovalItem
    ai_job: ProductionAiJobItem
    updated_at: datetime


class ProductionQueueResponse(BaseModel):
    items: list[ProductionQueueItem]
    page: int
    page_size: int
    total: int


class ProductionMetricsResponse(BaseModel):
    range: MetricsRangeLiteral
    scripts_approved: int
    versions_created: int
    quality_reviews_completed: int
    average_quality_score: float | None = None
    ai_jobs_completed: int
    ai_jobs_failed: int
    estimated_ai_cost: float
    average_days_to_approval: float | None = None


class ProductionActivityItem(BaseModel):
    id: UUID
    action: str
    action_label: str
    entity_type: str
    entity_id: UUID | None = None
    actor_user_id: UUID | None = None
    created_at: datetime
    metadata: dict[str, object] | None = None


class ProductionActivityResponse(BaseModel):
    items: list[ProductionActivityItem]
    restricted: bool = False


class ProductionSessionToday(BaseModel):
    goal: int
    completed: int
    estimated_finish: str | None = None
    current_streak: int = 0


class ProductionSessionProgress(BaseModel):
    approved_total: int
    approved_target: int
    remaining: int
    completion_percent: float
    approved_today: int


class ProductionSessionTimelineStep(BaseModel):
    key: str
    label: str
    status: Literal["complete", "current", "upcoming"]


class ProductionSessionSidebar(BaseModel):
    wave: int | None = None
    priority: str | None = None
    estimated_remaining_minutes: int = 0
    quality_score: int | None = None
    quality_band: str | None = None
    approval_status: str | None = None
    knowledge_pack_status: str
    knowledge_pack_completion: int = 0
    version_status: str | None = None
    reviewer: str | None = None


class ProductionSessionCurrent(BaseModel):
    topic_title: str
    topic_id: str | None = None
    topic_slug: str | None = None
    project_id: str
    project_code: str
    project_name: str
    script_id: str | None = None
    script_title: str | None = None
    production_stage: ProductionStageLiteral
    stage_label: str
    next_action: ProductionNextAction
    continue_url: str | None = None
    wave: int | None = None
    priority: str | None = None
    estimated_remaining_steps: int = 0
    timeline: list[ProductionSessionTimelineStep]
    sidebar: ProductionSessionSidebar | None = None


class ProductionSessionQueueItem(BaseModel):
    topic_title: str
    topic_id: str | None = None
    topic_slug: str | None = None
    project_id: str
    project_code: str
    project_name: str
    script_id: str | None = None
    script_title: str | None = None
    production_stage: ProductionStageLiteral
    stage_label: str
    next_action: ProductionNextAction
    continue_url: str | None = None
    wave: int | None = None
    priority: str | None = None
    estimated_remaining_steps: int = 0
    timeline: list[ProductionSessionTimelineStep]


class ProductionSessionPrevious(BaseModel):
    topic_title: str
    stage_label: str
    project_id: str
    script_id: str | None = None


class ProductionSessionSettingsSnippet(BaseModel):
    daily_approved_script_target: int
    approved_script_target: int


class ProductionSessionResponse(BaseModel):
    today: ProductionSessionToday
    progress: ProductionSessionProgress
    current: ProductionSessionCurrent | None = None
    upcoming: list[ProductionSessionQueueItem]
    previous_completed: ProductionSessionPrevious | None = None
    warnings: list[str]
    empty: bool
    browse_topics_url: str
    settings: ProductionSessionSettingsSnippet


PRODUCTION_STAGE_SET: frozenset[str] = frozenset(PRODUCTION_STAGES)
QUALITY_BAND_SET: frozenset[str] = frozenset(
    {
        "excellent",
        "strong",
        "needs_refinement",
        "weak",
        "major_revision_required",
    }
)
