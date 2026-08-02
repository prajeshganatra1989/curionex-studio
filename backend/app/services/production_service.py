"""Production Mode aggregation service — overview, queue, metrics, settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.constants import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    PROVIDER_OPENAI,
)
from app.ai.script_draft import (
    DEFAULT_BRAND_VOICE,
    content_fingerprint,
)
from app.ai.script_quality_review import PURPOSE_QUALITY_REVIEW, policy_fingerprint
from app.audit.actions import (
    ACTION_AI_JOB_COMPLETED,
    ACTION_AI_JOB_FAILED,
    ACTION_APPROVAL_APPROVED,
    ACTION_APPROVAL_REJECTED,
    ACTION_APPROVAL_REQUESTED,
    ACTION_CONTENT_VERSION_CREATED,
    ACTION_KNOWLEDGE_PACK_CREATED,
    ACTION_KNOWLEDGE_PACK_SECTION_UPDATED,
    ACTION_KNOWLEDGE_PACK_UPDATED,
    ACTION_PRODUCTION_SETTINGS_UPDATED,
    ACTION_SCRIPT_AI_DRAFT_APPLIED,
    ACTION_SCRIPT_AI_DRAFT_COMPLETED,
    ACTION_SCRIPT_CREATED,
    ACTION_SCRIPT_DOCUMENT_UPDATED,
    ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED,
    ACTION_SCRIPT_QUALITY_REVIEW_FAILED,
    ACTION_WORKFLOW_COMPLETED,
    ACTION_WORKFLOW_REVIEW_SUBMITTED,
    ACTION_WORKFLOW_VERSION_CREATED,
    ENTITY_PRODUCTION_SETTINGS,
)
from app.content_versions.constants import (
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
)
from app.knowledge_packs.catalog import SECTION_CATALOG
from app.models.ai import AiGeneration, AiJob, AiProvider, AiSettings
from app.models.audit import AuditLog
from app.models.content_version import Approval, ContentVersion
from app.models.knowledge_pack import KnowledgePack, KnowledgePackSection
from app.models.production import ProductionSettings
from app.models.project import Project, ProjectMember
from app.models.script import Script, ScriptDocument
from app.models.user import User
from app.models.workflow import ContentWorkflow
from app.production.stages import (
    DEFAULT_APPROVED_TARGET,
    DEFAULT_DAILY_TARGET,
    DEFAULT_WEEKLY_TARGET,
    STAGE_PRIORITY,
    AiJobSnapshot,
    ApprovalSnapshot,
    ClassificationInput,
    DocumentPresence,
    ProductionStage,
    QualitySnapshot,
    VersionFingerprintSnapshot,
    WorkflowSnapshot,
    classify_production_stage,
    empty_stage_counts,
    resolve_next_action,
    serialize_next_action,
)
from app.schemas.production import ProductionSettingsUpdate
from app.scripts.catalog import DOCUMENT_TYPES
from app.services.audit_service import record_audit_event
from app.services.rbac_service import has_permission
from app.workflows.snapshot import SnapshotValidationError, build_workspace_snapshot

MetricsRange = Literal["today", "7d", "30d"]

SECTION_COUNT = len(SECTION_CATALOG)

PRODUCTION_ACTIVITY_ACTIONS: frozenset[str] = frozenset(
    {
        ACTION_KNOWLEDGE_PACK_CREATED,
        ACTION_KNOWLEDGE_PACK_UPDATED,
        ACTION_KNOWLEDGE_PACK_SECTION_UPDATED,
        ACTION_SCRIPT_CREATED,
        ACTION_SCRIPT_DOCUMENT_UPDATED,
        ACTION_SCRIPT_AI_DRAFT_COMPLETED,
        ACTION_SCRIPT_AI_DRAFT_APPLIED,
        ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED,
        ACTION_SCRIPT_QUALITY_REVIEW_FAILED,
        ACTION_CONTENT_VERSION_CREATED,
        ACTION_WORKFLOW_VERSION_CREATED,
        ACTION_APPROVAL_REQUESTED,
        ACTION_APPROVAL_APPROVED,
        ACTION_APPROVAL_REJECTED,
        ACTION_WORKFLOW_REVIEW_SUBMITTED,
        ACTION_WORKFLOW_COMPLETED,
        ACTION_AI_JOB_COMPLETED,
        ACTION_AI_JOB_FAILED,
        ACTION_PRODUCTION_SETTINGS_UPDATED,
    }
)

ACTION_LABELS: dict[str, str] = {
    ACTION_KNOWLEDGE_PACK_CREATED: "Knowledge Pack created",
    ACTION_KNOWLEDGE_PACK_UPDATED: "Knowledge Pack updated",
    ACTION_KNOWLEDGE_PACK_SECTION_UPDATED: "Knowledge Pack section updated",
    ACTION_SCRIPT_CREATED: "Script created",
    ACTION_SCRIPT_DOCUMENT_UPDATED: "Script document updated",
    ACTION_SCRIPT_AI_DRAFT_COMPLETED: "AI draft generated",
    ACTION_SCRIPT_AI_DRAFT_APPLIED: "AI draft applied",
    ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED: "Quality review completed",
    ACTION_SCRIPT_QUALITY_REVIEW_FAILED: "Quality review failed",
    ACTION_CONTENT_VERSION_CREATED: "Content version created",
    ACTION_WORKFLOW_VERSION_CREATED: "Workflow version created",
    ACTION_APPROVAL_REQUESTED: "Human review requested",
    ACTION_APPROVAL_APPROVED: "Script approved",
    ACTION_APPROVAL_REJECTED: "Approval rejected",
    ACTION_WORKFLOW_REVIEW_SUBMITTED: "Submitted for human review",
    ACTION_WORKFLOW_COMPLETED: "Workflow completed",
    ACTION_AI_JOB_COMPLETED: "AI job completed",
    ACTION_AI_JOB_FAILED: "AI job failed",
    ACTION_PRODUCTION_SETTINGS_UPDATED: "Production settings updated",
}


class NotFoundError(Exception):
    """Raised when a requested entity cannot be found."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


@dataclass
class _DocState:
    discovery_brief: str = ""
    story_spine: str = ""
    master_script: str = ""
    discovery_present: bool = False
    story_present: bool = False
    master_present: bool = False


@dataclass
class _KpState:
    pack_id: UUID | None = None
    completion_percent: int = 0
    complete: bool = False
    section_hashes: dict[str, str] = field(default_factory=dict)


@dataclass
class ClassifiedUnit:
    """One classified production unit (script or project-without-script)."""

    project: Project
    script: Script | None
    stage: ProductionStage
    classification: ClassificationInput
    next_action: dict[str, Any]
    knowledge_pack_id: UUID | None
    knowledge_pack_completion: int
    document_statuses: dict[str, str]
    updated_at: datetime


def get_or_create_settings(db: Session) -> ProductionSettings:
    row = db.scalar(select(ProductionSettings).limit(1))
    if row is None:
        row = ProductionSettings(
            approved_script_target=DEFAULT_APPROVED_TARGET,
            daily_approved_script_target=DEFAULT_DAILY_TARGET,
            weekly_approved_script_target=DEFAULT_WEEKLY_TARGET,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(
    db: Session,
    payload: ProductionSettingsUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ProductionSettings:
    settings_row = get_or_create_settings(db)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise ValidationError("No settings fields provided.")

    changed: dict[str, dict[str, int]] = {}
    for field_name, new_value in data.items():
        if new_value is None:
            continue
        old_value = getattr(settings_row, field_name)
        if old_value != new_value:
            changed[field_name] = {"old": old_value, "new": new_value}
            setattr(settings_row, field_name, new_value)

    if not changed:
        return settings_row

    settings_row.updated_by = actor.id
    db.flush()
    record_audit_event(
        db,
        action=ACTION_PRODUCTION_SETTINGS_UPDATED,
        entity_type=ENTITY_PRODUCTION_SETTINGS,
        entity_id=settings_row.id,
        actor_user_id=actor.id,
        metadata={"changed_fields": changed},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(settings_row)
    return settings_row


def get_accessible_project_ids(db: Session, user: User) -> set[UUID]:
    """Return project IDs the user can access via ProjectMember (approvals pattern)."""
    rows = db.scalars(
        select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)
    ).all()
    return set(rows)


def _start_of_today(now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    return current.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_week(now: datetime | None = None) -> datetime:
    today = _start_of_today(now)
    # Monday-start week.
    return today - timedelta(days=today.weekday())


def _range_start(range_key: MetricsRange, now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    today = _start_of_today(current)
    if range_key == "today":
        return today
    if range_key == "7d":
        return today - timedelta(days=6)
    if range_key == "30d":
        return today - timedelta(days=29)
    raise ValidationError("range must be one of: today, 7d, 30d")


def _document_status(content: str | None, *, present: bool) -> str:
    if not present:
        return "missing"
    if (content or "").strip():
        return "complete"
    return "incomplete"


def _kp_completion(sections: list[KnowledgePackSection]) -> tuple[int, bool, dict[str, str]]:
    by_key = {s.section_key: s for s in sections}
    filled = 0
    hashes: dict[str, str] = {}
    for definition in SECTION_CATALOG:
        section = by_key.get(definition.key)
        content = (section.content if section else "") or ""
        hashes[definition.key] = content_fingerprint(content)
        if content.strip():
            filled += 1
    percent = int(round((filled / SECTION_COUNT) * 100)) if SECTION_COUNT else 0
    return percent, filled >= SECTION_COUNT and SECTION_COUNT > 0, hashes


def _openai_provider_blocker(db: Session) -> bool:
    provider = db.scalar(
        select(AiProvider).where(AiProvider.code == PROVIDER_OPENAI).limit(1)
    )
    if provider is None:
        return True
    return not bool(provider.encrypted_api_key)


def _brand_voice(db: Session) -> str:
    settings = db.scalar(select(AiSettings).limit(1))
    if settings is None or not (settings.brand_voice or "").strip():
        return DEFAULT_BRAND_VOICE.strip()
    return settings.brand_voice.strip()


def _quality_stale(
    generation: AiGeneration,
    *,
    docs: _DocState,
    section_hashes: dict[str, str],
    brand_voice: str,
    knowledge_pack_id: UUID | None,
) -> bool:
    stored = generation.input_fingerprint_json or {}
    if not stored:
        return False
    current = {
        "master_script": content_fingerprint(docs.master_script),
        "discovery_brief": content_fingerprint(docs.discovery_brief),
        "story_spine": content_fingerprint(docs.story_spine),
        "knowledge_pack_id": str(knowledge_pack_id) if knowledge_pack_id else None,
        "knowledge_pack_section_hashes": section_hashes,
        "brand_voice": content_fingerprint(brand_voice),
        "review_policy": policy_fingerprint(),
        "prompt_version_id": str(generation.prompt_version_id),
    }
    return current != stored


def _extract_quality(generation: AiGeneration | None, *, stale: bool) -> QualitySnapshot:
    if generation is None:
        return QualitySnapshot(stale=False)
    structured = generation.structured_output_json or {}
    score = structured.get("overall_score")
    score_int = int(score) if isinstance(score, (int, float)) else None
    band = structured.get("quality_band")
    recommendation = structured.get("recommended_next_action")
    risks = structured.get("factual_risks") or []
    issues = structured.get("priority_issues") or []
    high_risk = 0
    if isinstance(risks, list):
        high_risk = sum(
            1
            for risk in risks
            if isinstance(risk, dict) and risk.get("risk_level") == "high"
        )
    has_critical = False
    if isinstance(issues, list):
        has_critical = any(
            isinstance(issue, dict) and issue.get("severity") == "critical"
            for issue in issues
        )
    return QualitySnapshot(
        generation_id=generation.id,
        score=score_int,
        band=str(band) if band is not None else None,
        recommendation=str(recommendation) if recommendation is not None else None,
        stale=stale,
        high_risk_facts=high_risk,
        has_critical_issue=has_critical,
    )


def _workspace_matches_version(
    docs: list[ScriptDocument], version: ContentVersion | None
) -> bool | None:
    if version is None:
        return None
    try:
        snapshot = build_workspace_snapshot(docs)
    except SnapshotValidationError:
        return False
    return content_fingerprint(snapshot) == content_fingerprint(version.content or "")


def _load_classification_context(
    db: Session, *, project_ids: set[UUID]
) -> dict[str, Any]:
    if not project_ids:
        return {
            "projects": [],
            "scripts": [],
            "docs_by_script": {},
            "workflows": {},
            "versions_by_script": {},
            "pending_approvals": {},
            "quality_by_script": {},
            "jobs_by_script": {},
            "packs_by_project": {},
            "sections_by_pack": {},
            "brand_voice": DEFAULT_BRAND_VOICE.strip(),
            "provider_blocker": False,
        }

    projects = list(
        db.scalars(
            select(Project)
            .where(Project.id.in_(project_ids))
            .options(selectinload(Project.project_tags))
        ).all()
    )
    scripts = list(
        db.scalars(
            select(Script)
            .where(Script.project_id.in_(project_ids))
            .order_by(Script.updated_at.desc())
        ).all()
    )
    script_ids = [script.id for script in scripts]

    docs_by_script: dict[UUID, list[ScriptDocument]] = {sid: [] for sid in script_ids}
    if script_ids:
        documents = list(
            db.scalars(
                select(ScriptDocument).where(ScriptDocument.script_id.in_(script_ids))
            ).all()
        )
        for document in documents:
            docs_by_script.setdefault(document.script_id, []).append(document)

    workflows: dict[UUID, ContentWorkflow] = {}
    if script_ids:
        for workflow in db.scalars(
            select(ContentWorkflow).where(ContentWorkflow.script_id.in_(script_ids))
        ).all():
            workflows[workflow.script_id] = workflow

    versions_by_script: dict[UUID, ContentVersion] = {}
    if script_ids:
        versions = list(
            db.scalars(
                select(ContentVersion)
                .where(ContentVersion.script_id.in_(script_ids))
                .order_by(ContentVersion.created_at.desc())
            ).all()
        )
        for version in versions:
            if version.script_id is None:
                continue
            if version.script_id not in versions_by_script:
                versions_by_script[version.script_id] = version

        # Prefer workflow active version when present.
        active_ids = [
            wf.active_content_version_id
            for wf in workflows.values()
            if wf.active_content_version_id is not None
        ]
        if active_ids:
            active_versions = {
                v.id: v
                for v in db.scalars(
                    select(ContentVersion).where(ContentVersion.id.in_(active_ids))
                ).all()
            }
            for script_id, workflow in workflows.items():
                if workflow.active_content_version_id in active_versions:
                    versions_by_script[script_id] = active_versions[
                        workflow.active_content_version_id
                    ]

    pending_approvals: dict[UUID, Approval] = {}
    version_ids = [v.id for v in versions_by_script.values()]
    if version_ids:
        approvals = list(
            db.scalars(
                select(Approval)
                .where(
                    Approval.content_version_id.in_(version_ids),
                    Approval.status == APPROVAL_STATUS_PENDING,
                )
                .order_by(Approval.created_at.desc())
            ).all()
        )
        version_to_script = {v.id: sid for sid, v in versions_by_script.items()}
        for approval in approvals:
            script_id = version_to_script.get(approval.content_version_id)
            if script_id is not None and script_id not in pending_approvals:
                pending_approvals[script_id] = approval

    quality_by_script: dict[UUID, AiGeneration] = {}
    if script_ids:
        generations = list(
            db.scalars(
                select(AiGeneration)
                .where(
                    AiGeneration.script_id.in_(script_ids),
                    AiGeneration.purpose == PURPOSE_QUALITY_REVIEW,
                )
                .order_by(AiGeneration.created_at.desc())
            ).all()
        )
        for generation in generations:
            if generation.script_id is None:
                continue
            if generation.script_id not in quality_by_script:
                quality_by_script[generation.script_id] = generation

    jobs_by_script: dict[UUID, AiJob] = {}
    if script_ids:
        jobs = list(
            db.scalars(
                select(AiJob)
                .where(
                    AiJob.script_id.in_(script_ids),
                    AiJob.status.in_(
                        (JOB_STATUS_FAILED, JOB_STATUS_RUNNING, JOB_STATUS_QUEUED)
                    ),
                )
                .order_by(AiJob.created_at.desc())
            ).all()
        )
        # Prefer failed over running/queued when both exist recently.
        for job in jobs:
            if job.script_id is None:
                continue
            existing = jobs_by_script.get(job.script_id)
            if existing is None:
                jobs_by_script[job.script_id] = job
                continue
            if existing.status != JOB_STATUS_FAILED and job.status == JOB_STATUS_FAILED:
                jobs_by_script[job.script_id] = job

    packs = list(
        db.scalars(
            select(KnowledgePack)
            .where(KnowledgePack.project_id.in_(project_ids))
            .order_by(KnowledgePack.updated_at.desc())
        ).all()
    )
    packs_by_project: dict[UUID, list[KnowledgePack]] = {}
    pack_ids: list[UUID] = []
    for pack in packs:
        packs_by_project.setdefault(pack.project_id, []).append(pack)
        pack_ids.append(pack.id)

    sections_by_pack: dict[UUID, list[KnowledgePackSection]] = {
        pid: [] for pid in pack_ids
    }
    if pack_ids:
        sections = list(
            db.scalars(
                select(KnowledgePackSection).where(
                    KnowledgePackSection.knowledge_pack_id.in_(pack_ids)
                )
            ).all()
        )
        for section in sections:
            sections_by_pack.setdefault(section.knowledge_pack_id, []).append(section)

    return {
        "projects": projects,
        "scripts": scripts,
        "docs_by_script": docs_by_script,
        "workflows": workflows,
        "versions_by_script": versions_by_script,
        "pending_approvals": pending_approvals,
        "quality_by_script": quality_by_script,
        "jobs_by_script": jobs_by_script,
        "packs_by_project": packs_by_project,
        "sections_by_pack": sections_by_pack,
        "brand_voice": _brand_voice(db),
        "provider_blocker": _openai_provider_blocker(db),
    }


def _doc_state(documents: list[ScriptDocument]) -> _DocState:
    by_type = {doc.document_type: doc for doc in documents}
    state = _DocState()
    for doc_type in DOCUMENT_TYPES:
        document = by_type.get(doc_type)
        content = (document.content if document else "") or ""
        if doc_type == "discovery_brief":
            state.discovery_brief = content
            state.discovery_present = document is not None
        elif doc_type == "story_spine":
            state.story_spine = content
            state.story_present = document is not None
        elif doc_type == "master_script":
            state.master_script = content
            state.master_present = document is not None
    return state


def _resolve_kp_for_script(
    script: Script,
    *,
    packs_by_project: dict[UUID, list[KnowledgePack]],
    sections_by_pack: dict[UUID, list[KnowledgePackSection]],
) -> _KpState:
    """Resolve KP for display/completion. Prefer script link, else latest project pack."""
    linked_id = script.knowledge_pack_id
    display_id = linked_id
    if display_id is None:
        project_packs = packs_by_project.get(script.project_id) or []
        if project_packs:
            display_id = project_packs[0].id
    if display_id is None:
        return _KpState()

    display_sections = sections_by_pack.get(display_id) or []
    percent, complete, _display_hashes = _kp_completion(display_sections)

    # Stale fingerprints must match quality-review input (script-linked pack only).
    if linked_id is None:
        fingerprint_hashes: dict[str, str] = {}
    else:
        linked_sections = sections_by_pack.get(linked_id) or []
        _p, _c, fingerprint_hashes = _kp_completion(linked_sections)

    return _KpState(
        pack_id=display_id,
        completion_percent=percent,
        complete=complete,
        section_hashes=fingerprint_hashes,
    )


def _resolve_kp_for_project(
    project_id: UUID,
    *,
    packs_by_project: dict[UUID, list[KnowledgePack]],
    sections_by_pack: dict[UUID, list[KnowledgePackSection]],
) -> _KpState:
    project_packs = packs_by_project.get(project_id) or []
    if not project_packs:
        return _KpState()
    pack = project_packs[0]
    sections = sections_by_pack.get(pack.id) or []
    percent, complete, hashes = _kp_completion(sections)
    return _KpState(
        pack_id=pack.id,
        completion_percent=percent,
        complete=complete,
        section_hashes=hashes,
    )


def _build_classified_units(
    db: Session,
    user: User,
    *,
    include_project_only: bool = False,
    project_id: UUID | None = None,
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    search: str | None = None,
) -> list[ClassifiedUnit]:
    accessible = get_accessible_project_ids(db, user)
    if project_id is not None:
        if project_id not in accessible:
            return []
        accessible = {project_id}

    if not accessible:
        return []

    ctx = _load_classification_context(db, project_ids=accessible)
    projects: list[Project] = ctx["projects"]
    scripts: list[Script] = ctx["scripts"]

    if category_id is not None:
        projects = [p for p in projects if p.category_id == category_id]
        project_filter = {p.id for p in projects}
        scripts = [s for s in scripts if s.project_id in project_filter]

    if tag_id is not None:
        projects = [
            p
            for p in projects
            if any(link.tag_id == tag_id for link in (p.project_tags or []))
        ]
        project_filter = {p.id for p in projects}
        scripts = [s for s in scripts if s.project_id in project_filter]

    if search:
        term = search.strip().lower()
        if term:
            project_by_id = {p.id: p for p in projects}

            def matches(script: Script) -> bool:
                project = project_by_id.get(script.project_id)
                haystacks = [
                    script.script_code or "",
                    script.title or "",
                    project.project_code if project else "",
                    project.name if project else "",
                ]
                return any(term in value.lower() for value in haystacks)

            scripts = [s for s in scripts if matches(s)]
            if include_project_only:
                projects = [
                    p
                    for p in projects
                    if term in p.project_code.lower() or term in p.name.lower()
                ]

    project_by_id = {p.id: p for p in projects}
    units: list[ClassifiedUnit] = []
    scripts_by_project: dict[UUID, list[Script]] = {}

    for script in scripts:
        project = project_by_id.get(script.project_id)
        if project is None:
            continue
        scripts_by_project.setdefault(project.id, []).append(script)

        documents = ctx["docs_by_script"].get(script.id, [])
        docs = _doc_state(documents)
        kp = _resolve_kp_for_script(
            script,
            packs_by_project=ctx["packs_by_project"],
            sections_by_pack=ctx["sections_by_pack"],
        )
        generation = ctx["quality_by_script"].get(script.id)
        stale = False
        if generation is not None:
            stale = _quality_stale(
                generation,
                docs=docs,
                section_hashes=kp.section_hashes,
                brand_voice=ctx["brand_voice"],
                knowledge_pack_id=script.knowledge_pack_id,
            )
        quality = _extract_quality(generation, stale=stale)
        workflow = ctx["workflows"].get(script.id)
        version = ctx["versions_by_script"].get(script.id)
        approval = ctx["pending_approvals"].get(script.id)
        job = ctx["jobs_by_script"].get(script.id)
        matches = _workspace_matches_version(documents, version)

        classification = ClassificationInput(
            script_id=script.id,
            project_id=project.id,
            project_status=project.status,
            script_status=script.status,
            has_knowledge_pack=kp.pack_id is not None,
            knowledge_pack_complete=kp.complete,
            knowledge_pack_completion_percent=kp.completion_percent,
            documents=DocumentPresence(
                discovery_brief=bool(docs.discovery_brief.strip()),
                story_spine=bool(docs.story_spine.strip()),
                master_script=bool(docs.master_script.strip()),
            ),
            quality=quality,
            workflow=WorkflowSnapshot(
                stage=workflow.current_stage if workflow else None,
                status=workflow.status if workflow else None,
                active_version_id=(
                    workflow.active_content_version_id if workflow else None
                ),
            ),
            approval=ApprovalSnapshot(
                status=approval.status if approval else None,
                approval_id=approval.id if approval else None,
            ),
            ai_job=AiJobSnapshot(
                status=job.status if job else None,
                job_id=job.id if job else None,
                purpose=job.purpose if job else None,
                error_message=job.error_message if job else None,
            ),
            version=VersionFingerprintSnapshot(
                version_id=version.id if version else None,
                version_status=version.status if version else None,
                workspace_matches_version=matches,
            ),
            provider_config_blocker=ctx["provider_blocker"],
        )
        stage = classify_production_stage(classification)
        action = resolve_next_action(
            stage,
            project_id=project.id,
            script_id=script.id,
            knowledge_pack_id=kp.pack_id,
            quality_generation_id=quality.generation_id,
            approval_id=approval.id if approval else None,
            version_id=version.id if version else None,
            failed_job_id=(
                job.id if job is not None and job.status == JOB_STATUS_FAILED else None
            ),
            provider_config_blocker=ctx["provider_blocker"],
        )
        units.append(
            ClassifiedUnit(
                project=project,
                script=script,
                stage=stage,
                classification=classification,
                next_action=serialize_next_action(action),
                knowledge_pack_id=kp.pack_id,
                knowledge_pack_completion=kp.completion_percent,
                document_statuses={
                    "discovery_brief": _document_status(
                        docs.discovery_brief, present=docs.discovery_present
                    ),
                    "story_spine": _document_status(
                        docs.story_spine, present=docs.story_present
                    ),
                    "master_script": _document_status(
                        docs.master_script, present=docs.master_present
                    ),
                },
                updated_at=script.updated_at,
            )
        )

    if include_project_only:
        for project in projects:
            if scripts_by_project.get(project.id):
                continue
            kp = _resolve_kp_for_project(
                project.id,
                packs_by_project=ctx["packs_by_project"],
                sections_by_pack=ctx["sections_by_pack"],
            )
            classification = ClassificationInput(
                script_id=None,
                project_id=project.id,
                project_status=project.status,
                has_knowledge_pack=kp.pack_id is not None,
                knowledge_pack_complete=kp.complete,
                knowledge_pack_completion_percent=kp.completion_percent,
                provider_config_blocker=False,
            )
            stage = classify_production_stage(classification)
            action = resolve_next_action(
                stage,
                project_id=project.id,
                script_id=None,
                knowledge_pack_id=kp.pack_id,
            )
            units.append(
                ClassifiedUnit(
                    project=project,
                    script=None,
                    stage=stage,
                    classification=classification,
                    next_action=serialize_next_action(action),
                    knowledge_pack_id=kp.pack_id,
                    knowledge_pack_completion=kp.completion_percent,
                    document_statuses={
                        "discovery_brief": "missing",
                        "story_spine": "missing",
                        "master_script": "missing",
                    },
                    updated_at=project.updated_at,
                )
            )

    return units


def _unit_to_queue_item(unit: ClassifiedUnit) -> dict[str, Any]:
    script = unit.script
    quality = unit.classification.quality
    workflow = unit.classification.workflow
    approval = unit.classification.approval
    ai_job = unit.classification.ai_job
    return {
        "script_id": script.id if script else None,
        "project_id": unit.project.id,
        "project_code": unit.project.project_code,
        "project_name": unit.project.name,
        "script_code": script.script_code if script else None,
        "script_title": script.title if script else None,
        "script_status": script.status if script else None,
        "production_stage": unit.stage,
        "next_action": unit.next_action,
        "knowledge_pack_id": unit.knowledge_pack_id,
        "knowledge_pack_completion": unit.knowledge_pack_completion,
        "documents": unit.document_statuses,
        "quality": {
            "score": quality.score,
            "band": quality.band,
            "stale": quality.stale,
            "recommendation": quality.recommendation,
            "generation_id": quality.generation_id,
            "high_risk_facts": quality.high_risk_facts,
        },
        "workflow": {
            "stage": workflow.stage,
            "status": workflow.status,
            "active_version_id": workflow.active_version_id,
        },
        "approval": {
            "status": approval.status,
            "approval_id": approval.approval_id,
        },
        "ai_job": {
            "status": ai_job.status,
            "job_id": ai_job.job_id,
            "purpose": ai_job.purpose,
            "error_message": ai_job.error_message,
        },
        "updated_at": unit.updated_at,
    }


def build_overview(db: Session, user: User) -> dict[str, Any]:
    settings = get_or_create_settings(db)
    units = _build_classified_units(db, user, include_project_only=True)
    stage_counts = empty_stage_counts()
    for unit in units:
        stage_counts[unit.stage] = stage_counts.get(unit.stage, 0) + 1

    approved_total = stage_counts.get("approved", 0)
    target = settings.approved_script_target
    remaining = max(target - approved_total, 0)
    completion_percent = (
        round((approved_total / target) * 100, 1) if target > 0 else 0.0
    )

    accessible = get_accessible_project_ids(db, user)
    today_start = _start_of_today()
    week_start = _start_of_week()

    approved_today = 0
    approved_this_week = 0
    if accessible:
        approved_rows = list(
            db.execute(
                select(Approval.reviewed_at, ContentVersion.script_id)
                .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
                .where(
                    ContentVersion.project_id.in_(accessible),
                    Approval.status == APPROVAL_STATUS_APPROVED,
                    Approval.reviewed_at.is_not(None),
                )
            ).all()
        )
        # Deduplicate by script_id (prefer latest approval timestamp already unordered).
        latest_by_script: dict[UUID | None, datetime] = {}
        for reviewed_at, script_id in approved_rows:
            if reviewed_at is None:
                continue
            previous = latest_by_script.get(script_id)
            if previous is None or reviewed_at > previous:
                latest_by_script[script_id] = reviewed_at
        for reviewed_at in latest_by_script.values():
            if reviewed_at >= today_start:
                approved_today += 1
            if reviewed_at >= week_start:
                approved_this_week += 1

    # AI job aggregates for accessible projects.
    queued = running = failed = completed_today = 0
    cost_today = 0.0
    cost_week = 0.0
    if accessible:
        job_rows = db.execute(
            select(AiJob.status, func.count())
            .where(
                AiJob.project_id.in_(accessible),
                AiJob.status.in_(
                    (JOB_STATUS_QUEUED, JOB_STATUS_RUNNING, JOB_STATUS_FAILED)
                ),
            )
            .group_by(AiJob.status)
        ).all()
        counts = {status: int(count) for status, count in job_rows}
        queued = counts.get(JOB_STATUS_QUEUED, 0)
        running = counts.get(JOB_STATUS_RUNNING, 0)
        failed = counts.get(JOB_STATUS_FAILED, 0)
        completed_today = int(
            db.scalar(
                select(func.count())
                .select_from(AiJob)
                .where(
                    AiJob.project_id.in_(accessible),
                    AiJob.status == JOB_STATUS_COMPLETED,
                    AiJob.finished_at >= today_start,
                )
            )
            or 0
        )
        cost_today = float(
            db.scalar(
                select(func.coalesce(func.sum(AiGeneration.cost_usd), 0.0)).where(
                    AiGeneration.project_id.in_(accessible),
                    AiGeneration.created_at >= today_start,
                )
            )
            or 0.0
        )
        cost_week = float(
            db.scalar(
                select(func.coalesce(func.sum(AiGeneration.cost_usd), 0.0)).where(
                    AiGeneration.project_id.in_(accessible),
                    AiGeneration.created_at >= week_start,
                )
            )
            or 0.0
        )

    scores: list[int] = []
    scripts_needing_revision = 0
    stale_reviews = 0
    high_risk_fact_flags = 0
    for unit in units:
        if unit.script is None:
            continue
        if unit.stage == "needs_revision":
            scripts_needing_revision += 1
        quality = unit.classification.quality
        if quality.stale:
            stale_reviews += 1
        high_risk_fact_flags += quality.high_risk_facts
        if (
            quality.generation_id is not None
            and not quality.stale
            and quality.score is not None
        ):
            scores.append(quality.score)

    average_current_score = (
        round(sum(scores) / len(scores), 1) if scores else None
    )

    # Projection: average daily approvals over last 7 days (excluding today partial).
    projected_days_remaining: float | None = None
    if remaining > 0 and accessible:
        seven_days_ago = today_start - timedelta(days=7)
        recent_count = int(
            db.scalar(
                select(func.count())
                .select_from(Approval)
                .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
                .where(
                    ContentVersion.project_id.in_(accessible),
                    Approval.status == APPROVAL_STATUS_APPROVED,
                    Approval.reviewed_at >= seven_days_ago,
                    Approval.reviewed_at < today_start,
                )
            )
            or 0
        )
        if recent_count > 0:
            daily_avg = recent_count / 7.0
            if daily_avg > 0:
                projected_days_remaining = round(remaining / daily_avg, 1)

    return {
        "goals": {
            "approved_target": target,
            "approved_total": approved_total,
            "remaining": remaining,
            "completion_percent": completion_percent,
            "daily_target": settings.daily_approved_script_target,
            "approved_today": approved_today,
            "weekly_target": settings.weekly_approved_script_target,
            "approved_this_week": approved_this_week,
            "projected_days_remaining": projected_days_remaining,
        },
        "stage_counts": stage_counts,
        "ai": {
            "queued": queued,
            "running": running,
            "failed": failed,
            "completed_today": completed_today,
            "estimated_cost_today": round(cost_today, 4),
            "estimated_cost_this_week": round(cost_week, 4),
        },
        "quality": {
            "average_current_score": average_current_score,
            "scripts_needing_revision": scripts_needing_revision,
            "stale_reviews": stale_reviews,
            "high_risk_fact_flags": high_risk_fact_flags,
        },
    }


def build_queue(
    db: Session,
    user: User,
    *,
    production_stage: str | None = None,
    project_id: UUID | None = None,
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    search: str | None = None,
    quality_band: str | None = None,
    ai_job_status: str | None = None,
    stale_quality: bool | None = None,
    blocked_only: bool = False,
    pending_approval: bool = False,
    script_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    units = _build_classified_units(
        db,
        user,
        include_project_only=False,
        project_id=project_id,
        category_id=category_id,
        tag_id=tag_id,
        search=search,
    )

    filtered: list[ClassifiedUnit] = []
    for unit in units:
        if unit.script is None:
            continue
        if production_stage and unit.stage != production_stage:
            continue
        if blocked_only and unit.stage != "blocked":
            continue
        if pending_approval and unit.stage != "pending_human_review":
            continue
        if script_status and (unit.script.status or "") != script_status:
            continue
        if quality_band and (unit.classification.quality.band or "") != quality_band:
            continue
        if ai_job_status and (unit.classification.ai_job.status or "") != ai_job_status:
            continue
        if stale_quality is True and not unit.classification.quality.stale:
            continue
        if stale_quality is False and unit.classification.quality.stale:
            continue
        filtered.append(unit)

    sort_key = (sort or "priority").strip().lower()
    if sort_key == "updated_at":
        filtered.sort(key=lambda u: u.updated_at, reverse=True)
    elif sort_key == "stage":
        filtered.sort(
            key=lambda u: (STAGE_PRIORITY.get(u.stage, 99), -u.updated_at.timestamp())
        )
    else:
        # Default: STAGE_PRIORITY then updated_at desc.
        filtered.sort(
            key=lambda u: (STAGE_PRIORITY.get(u.stage, 99), -u.updated_at.timestamp())
        )

    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]
    return [_unit_to_queue_item(unit) for unit in page_items], total


def build_metrics(
    db: Session, user: User, *, range: MetricsRange = "7d"
) -> dict[str, Any]:
    if range not in {"today", "7d", "30d"}:
        raise ValidationError("range must be one of: today, 7d, 30d")

    accessible = get_accessible_project_ids(db, user)
    start = _range_start(range)
    if not accessible:
        return {
            "range": range,
            "scripts_approved": 0,
            "versions_created": 0,
            "quality_reviews_completed": 0,
            "average_quality_score": None,
            "ai_jobs_completed": 0,
            "ai_jobs_failed": 0,
            "estimated_ai_cost": 0.0,
            "average_days_to_approval": None,
        }

    scripts_approved = int(
        db.scalar(
            select(func.count(func.distinct(ContentVersion.script_id)))
            .select_from(Approval)
            .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
            .where(
                ContentVersion.project_id.in_(accessible),
                Approval.status == APPROVAL_STATUS_APPROVED,
                Approval.reviewed_at >= start,
                ContentVersion.script_id.is_not(None),
            )
        )
        or 0
    )
    versions_created = int(
        db.scalar(
            select(func.count())
            .select_from(ContentVersion)
            .where(
                ContentVersion.project_id.in_(accessible),
                ContentVersion.created_at >= start,
            )
        )
        or 0
    )
    quality_reviews_completed = int(
        db.scalar(
            select(func.count())
            .select_from(AiGeneration)
            .where(
                AiGeneration.project_id.in_(accessible),
                AiGeneration.purpose == PURPOSE_QUALITY_REVIEW,
                AiGeneration.created_at >= start,
                AiGeneration.structured_output_json.is_not(None),
            )
        )
        or 0
    )

    score_rows = db.scalars(
        select(AiGeneration.structured_output_json).where(
            AiGeneration.project_id.in_(accessible),
            AiGeneration.purpose == PURPOSE_QUALITY_REVIEW,
            AiGeneration.created_at >= start,
            AiGeneration.structured_output_json.is_not(None),
        )
    ).all()
    scores: list[int] = []
    for payload in score_rows:
        if not isinstance(payload, dict):
            continue
        score = payload.get("overall_score")
        if isinstance(score, (int, float)):
            scores.append(int(score))
    average_quality_score = (
        round(sum(scores) / len(scores), 1) if scores else None
    )

    ai_jobs_completed = int(
        db.scalar(
            select(func.count())
            .select_from(AiJob)
            .where(
                AiJob.project_id.in_(accessible),
                AiJob.status == JOB_STATUS_COMPLETED,
                AiJob.finished_at >= start,
            )
        )
        or 0
    )
    ai_jobs_failed = int(
        db.scalar(
            select(func.count())
            .select_from(AiJob)
            .where(
                AiJob.project_id.in_(accessible),
                AiJob.status == JOB_STATUS_FAILED,
                or_(AiJob.finished_at >= start, AiJob.created_at >= start),
            )
        )
        or 0
    )
    estimated_ai_cost = float(
        db.scalar(
            select(func.coalesce(func.sum(AiGeneration.cost_usd), 0.0)).where(
                AiGeneration.project_id.in_(accessible),
                AiGeneration.created_at >= start,
            )
        )
        or 0.0
    )

    duration_rows = db.execute(
        select(Approval.reviewed_at, Script.created_at)
        .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
        .join(Script, ContentVersion.script_id == Script.id)
        .where(
            ContentVersion.project_id.in_(accessible),
            Approval.status == APPROVAL_STATUS_APPROVED,
            Approval.reviewed_at >= start,
            Approval.reviewed_at.is_not(None),
        )
    ).all()
    durations: list[float] = []
    for reviewed_at, created_at in duration_rows:
        if reviewed_at is None or created_at is None:
            continue
        delta = (reviewed_at - created_at).total_seconds() / 86400.0
        if delta >= 0:
            durations.append(delta)
    average_days_to_approval = (
        round(sum(durations) / len(durations), 2) if durations else None
    )

    return {
        "range": range,
        "scripts_approved": scripts_approved,
        "versions_created": versions_created,
        "quality_reviews_completed": quality_reviews_completed,
        "average_quality_score": average_quality_score,
        "ai_jobs_completed": ai_jobs_completed,
        "ai_jobs_failed": ai_jobs_failed,
        "estimated_ai_cost": round(estimated_ai_cost, 4),
        "average_days_to_approval": average_days_to_approval,
    }


def list_recent_activity(
    db: Session, user: User, *, limit: int = 20
) -> dict[str, Any]:
    limit = min(max(limit, 1), 100)
    if not has_permission(db, user, "audit.view"):
        return {"items": [], "restricted": True}

    accessible = get_accessible_project_ids(db, user)
    stmt = (
        select(AuditLog)
        .where(AuditLog.action.in_(PRODUCTION_ACTIVITY_ACTIONS))
        .order_by(AuditLog.created_at.desc())
        .limit(limit * 3)
    )
    events = list(db.scalars(stmt).all())

    # Prefer events tied to accessible projects when metadata/project linkage exists.
    # Keep settings updates and events without project scope.
    items: list[dict[str, Any]] = []
    for event in events:
        metadata = event.event_metadata if isinstance(event.event_metadata, dict) else None
        project_id_raw = None
        if metadata:
            project_id_raw = metadata.get("project_id")
        if project_id_raw and accessible:
            try:
                pid = UUID(str(project_id_raw))
            except (TypeError, ValueError):
                pid = None
            if pid is not None and pid not in accessible:
                continue
        items.append(
            {
                "id": event.id,
                "action": event.action,
                "action_label": ACTION_LABELS.get(event.action, event.action),
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "actor_user_id": event.actor_user_id,
                "created_at": event.created_at,
                "metadata": metadata,
            }
        )
        if len(items) >= limit:
            break

    return {"items": items, "restricted": False}


__all__ = [
    "NotFoundError",
    "ValidationError",
    "build_metrics",
    "build_overview",
    "build_queue",
    "get_accessible_project_ids",
    "get_or_create_settings",
    "list_recent_activity",
    "update_settings",
]
