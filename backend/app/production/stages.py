"""Production Mode stage classification and next-action resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from uuid import UUID

from app.ai.script_draft import content_fingerprint

ProductionStage = Literal[
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

PRODUCTION_STAGES: tuple[ProductionStage, ...] = (
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
)

# Default queue priority (lower = higher priority).
STAGE_PRIORITY: dict[ProductionStage, int] = {
    "blocked": 0,
    "pending_human_review": 1,
    "needs_revision": 2,
    "quality_review": 3,  # includes stale via needs_revision/quality paths
    "ready_for_version": 4,
    "version_created": 5,
    "master_script": 6,
    "story_spine": 7,
    "discovery_brief": 8,
    "research": 9,
    "idea": 10,
    "approved": 11,
    "archived": 12,
}

DEFAULT_APPROVED_TARGET = 120
DEFAULT_DAILY_TARGET = 2
DEFAULT_WEEKLY_TARGET = 14
MAX_APPROVED_TARGET = 10000
MAX_DAILY_TARGET = 100
MAX_WEEKLY_TARGET = 700

HUMAN_REVIEW_SCORE_THRESHOLD = 80


@dataclass
class DocumentPresence:
    discovery_brief: bool = False
    story_spine: bool = False
    master_script: bool = False


@dataclass
class QualitySnapshot:
    generation_id: UUID | None = None
    score: int | None = None
    band: str | None = None
    recommendation: str | None = None
    stale: bool = False
    high_risk_facts: int = 0
    has_critical_issue: bool = False


@dataclass
class WorkflowSnapshot:
    stage: str | None = None
    status: str | None = None
    active_version_id: UUID | None = None


@dataclass
class ApprovalSnapshot:
    status: str | None = None
    approval_id: UUID | None = None


@dataclass
class AiJobSnapshot:
    status: str | None = None
    job_id: UUID | None = None
    purpose: str | None = None
    error_message: str | None = None


@dataclass
class VersionFingerprintSnapshot:
    version_id: UUID | None = None
    version_status: str | None = None
    workspace_matches_version: bool | None = None


@dataclass
class ClassificationInput:
    """All signals needed to derive one production stage."""

    script_id: UUID | None = None
    project_id: UUID | None = None
    project_status: str | None = None
    script_status: str | None = None
    has_knowledge_pack: bool = False
    knowledge_pack_complete: bool = False
    knowledge_pack_completion_percent: int = 0
    documents: DocumentPresence = field(default_factory=DocumentPresence)
    quality: QualitySnapshot = field(default_factory=QualitySnapshot)
    workflow: WorkflowSnapshot = field(default_factory=WorkflowSnapshot)
    approval: ApprovalSnapshot = field(default_factory=ApprovalSnapshot)
    ai_job: AiJobSnapshot = field(default_factory=AiJobSnapshot)
    version: VersionFingerprintSnapshot = field(
        default_factory=VersionFingerprintSnapshot
    )
    provider_config_blocker: bool = False


@dataclass
class NextAction:
    code: str
    label: str
    href: str | None
    reason: str
    blocked: bool = False


def workspace_documents_fingerprint(
    discovery: str, story: str, master: str
) -> str:
    blob = "\n---\n".join(
        [
            content_fingerprint(discovery or ""),
            content_fingerprint(story or ""),
            content_fingerprint(master or ""),
        ]
    )
    return content_fingerprint(blob)


def classify_production_stage(data: ClassificationInput) -> ProductionStage:
    """Deterministic stage precedence (first match wins).

    Precedence:
    1. archived
    2. approved
    3. blocked
    4. pending_human_review
    5. version_created
    6. needs_revision
    7. ready_for_version
    8. quality_review
    9. master_script
    10. story_spine
    11. discovery_brief
    12. research
    13. idea
    """
    if (data.script_status or "") == "archived" or (data.project_status or "") == "archived":
        return "archived"

    if data.script_id is None:
        if data.has_knowledge_pack and not data.knowledge_pack_complete:
            return "research"
        if data.has_knowledge_pack and data.knowledge_pack_complete:
            return "research"
        return "idea"

    workflow_completed = (data.workflow.stage or "") == "completed" or (
        data.workflow.status or ""
    ) == "completed"
    version_approved = (data.version.version_status or "") == "approved"
    script_approved = (data.script_status or "") == "approved"
    if workflow_completed or (version_approved and script_approved):
        return "approved"

    if data.provider_config_blocker:
        return "blocked"
    if (data.ai_job.status or "") == "failed":
        return "blocked"
    if (data.workflow.status or "") == "blocked":
        return "blocked"

    if (data.approval.status or "") == "pending":
        return "pending_human_review"

    if data.version.version_id is not None and (data.approval.status or "") != "pending":
        # Active/latest version exists and is not yet in human review.
        if (data.version.version_status or "") in {"draft", "in_review"}:
            if (data.version.version_status or "") == "draft":
                return "version_created"
            # in_review without pending approval is unusual — treat as pending if approval missing
            return "pending_human_review"
        if (data.version.version_status or "") == "rejected":
            return "needs_revision"

    # Quality / revision gates when Master Script exists.
    if data.documents.master_script:
        if data.quality.generation_id is None:
            return "quality_review"
        if data.quality.stale:
            return "needs_revision"
        if data.quality.recommendation == "revise":
            return "needs_revision"
        if data.quality.has_critical_issue or data.quality.high_risk_facts > 0:
            if data.quality.recommendation != "ready_for_version":
                return "needs_revision"
        if (data.quality.score is not None) and (
            data.quality.score < HUMAN_REVIEW_SCORE_THRESHOLD
        ):
            return "needs_revision"
        if data.quality.recommendation in {"ready_for_version", "human_review"}:
            # Workspace changed after version → need a new version.
            if data.version.workspace_matches_version is False:
                return "ready_for_version"
            if data.version.version_id is None:
                return "ready_for_version"
            return "ready_for_version"

    if not data.documents.master_script:
        if data.documents.story_spine:
            return "master_script"
        if data.documents.discovery_brief:
            return "story_spine"
        if data.has_knowledge_pack:
            return "discovery_brief"
        return "discovery_brief"

    # Master present but no quality generation handled above.
    return "quality_review"


def resolve_next_action(
    stage: ProductionStage,
    *,
    project_id: UUID | None,
    script_id: UUID | None,
    knowledge_pack_id: UUID | None = None,
    quality_generation_id: UUID | None = None,
    approval_id: UUID | None = None,
    version_id: UUID | None = None,
    failed_job_id: UUID | None = None,
    provider_config_blocker: bool = False,
) -> NextAction:
    pid = str(project_id) if project_id else None
    sid = str(script_id) if script_id else None

    def script_href(suffix: str = "") -> str | None:
        if not pid or not sid:
            return None
        return f"/projects/{pid}/scripts/{sid}{suffix}"

    if stage == "archived":
        return NextAction(
            code="view_approved_version",
            label="Open Archived Script",
            href=script_href(),
            reason="Script or project is archived.",
            blocked=True,
        )

    if provider_config_blocker:
        return NextAction(
            code="configure_ai_provider",
            label="Configure OpenAI",
            href="/ai/settings",
            reason="AI provider credentials or model configuration is missing.",
            blocked=True,
        )

    if stage == "blocked" and failed_job_id:
        return NextAction(
            code="retry_ai_job",
            label="Retry AI Job",
            href=f"/ai/jobs?job_id={failed_job_id}",
            reason="Latest AI job failed and requires attention.",
        )

    if stage == "blocked":
        return NextAction(
            code="resolve_blocker",
            label="Resolve Blocker",
            href=script_href() or (f"/projects/{pid}" if pid else "/production"),
            reason="Production is blocked by a workflow or configuration issue.",
            blocked=True,
        )

    if stage == "approved":
        href = script_href(f"/versions/{version_id}") if version_id else script_href()
        return NextAction(
            code="view_approved_version",
            label="View Approved Version",
            href=href,
            reason="Script has an approved version.",
        )

    if stage == "pending_human_review":
        if approval_id:
            return NextAction(
                code="review_approval",
                label="Review Version",
                href=f"/reviews/{approval_id}",
                reason="A human approval is pending.",
            )
        return NextAction(
            code="open_pending_review",
            label="Open Pending Review",
            href="/reviews",
            reason="A version is awaiting human review.",
        )

    if stage == "version_created":
        return NextAction(
            code="submit_human_review",
            label="Submit for Review",
            href=script_href(),
            reason="A ContentVersion exists and should be submitted for human review.",
        )

    if stage == "ready_for_version":
        return NextAction(
            code="create_version",
            label="Create Version",
            href=script_href(),
            reason="Workspace is ready for an immutable ContentVersion.",
        )

    if stage == "needs_revision":
        if quality_generation_id and pid and sid:
            return NextAction(
                code="fix_quality_issues",
                label="Fix Quality Issues",
                href=f"/projects/{pid}/scripts/{sid}/quality-reviews/{quality_generation_id}",
                reason="Latest quality review recommends revision or is stale.",
            )
        return NextAction(
            code="open_quality_review",
            label="Open Quality Review",
            href=script_href(),
            reason="Script needs editorial revision before versioning.",
        )

    if stage == "quality_review":
        return NextAction(
            code="run_quality_review",
            label="Run Quality Review",
            href=script_href(),
            reason="Master Script is ready for AI quality review.",
        )

    if stage == "master_script":
        return NextAction(
            code="generate_master_script",
            label="Generate Master Script",
            href=script_href(),
            reason="Story Spine is ready; Master Script is incomplete.",
        )

    if stage == "story_spine":
        return NextAction(
            code="generate_story_spine",
            label="Generate Story Spine",
            href=script_href(),
            reason="Discovery Brief is ready; Story Spine is incomplete.",
        )

    if stage == "discovery_brief":
        if script_id:
            return NextAction(
                code="generate_discovery_brief",
                label="Generate Discovery Brief",
                href=script_href(),
                reason="Script needs a Discovery Brief.",
            )
        return NextAction(
            code="create_script",
            label="Create Script",
            href=f"/projects/{pid}/scripts" if pid else "/projects",
            reason="Project is ready for its first Script.",
        )

    if stage == "research":
        if knowledge_pack_id and pid:
            return NextAction(
                code="open_knowledge_pack",
                label="Continue Research",
                href=f"/projects/{pid}/knowledge-packs/{knowledge_pack_id}",
                reason="Knowledge Pack research is incomplete.",
            )
        if pid:
            return NextAction(
                code="create_knowledge_pack",
                label="Create Knowledge Pack",
                href=f"/projects/{pid}/packs",
                reason="Project needs a Knowledge Pack.",
            )

    # idea
    if pid:
        return NextAction(
            code="create_knowledge_pack",
            label="Create Knowledge Pack",
            href=f"/projects/{pid}",
            reason="Start research for this Project.",
        )
    return NextAction(
        code="create_knowledge_pack",
        label="Create Project",
        href="/projects",
        reason="Start your 120-script journey with a new Project.",
    )


def empty_stage_counts() -> dict[str, int]:
    return {stage: 0 for stage in PRODUCTION_STAGES}


def serialize_next_action(action: NextAction) -> dict[str, Any]:
    return {
        "code": action.code,
        "label": action.label,
        "href": action.href,
        "reason": action.reason,
        "blocked": action.blocked,
    }
