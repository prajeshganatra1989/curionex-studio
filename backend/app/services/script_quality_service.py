"""Script AI quality review — prompt seeding, jobs, listing, and suggestion apply."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.ai.constants import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_QUEUED,
    PROMPT_STATUS_ACTIVE,
    PROMPT_VERSION_STATUS_ACTIVE,
    PROVIDER_OPENAI,
)
from app.ai.job_executor import execute_job
from app.ai.script_draft import (
    DEFAULT_BRAND_VOICE,
    DEFAULT_QUALITY_REQUIREMENTS,
    DEFAULT_TARGET_DURATION_SECONDS,
    DEFAULT_TARGET_WORDS_PER_MINUTE,
    content_fingerprint,
    word_count,
)
from app.ai.script_quality_review import (
    MAX_PRIORITY_ISSUES,
    PURPOSE_QUALITY_REVIEW,
    QUALITY_REVIEW_DOCUMENT_TYPE,
    SuggestionStrategy,
    policy_fingerprint,
)
from app.audit.actions import (
    ACTION_AI_PROMPT_CREATED,
    ACTION_AI_PROMPT_VERSION_CREATED,
    ACTION_SCRIPT_QUALITY_REVIEW_REQUESTED,
    ACTION_SCRIPT_QUALITY_SUGGESTION_APPLIED,
    ENTITY_AI_PROMPT,
    ENTITY_AI_PROMPT_VERSION,
    ENTITY_SCRIPT,
)
from app.models.ai import (
    AiGeneration,
    AiJob,
    AiModel,
    AiPrompt,
    AiPromptVersion,
    AiProvider,
)
from app.models.knowledge_pack import KnowledgePackSection
from app.models.project import Project
from app.models.script import Script, ScriptDocument
from app.models.user import User
from app.services import ai_service, script_service
from app.services.audit_service import record_audit_event

DEFAULT_LANGUAGE = "English"

PROMPT_NAME = "Script Quality Review"

SYSTEM_PROMPT = """You are Curionex Studio's editorial quality reviewer for short-form educational video narration.
Evaluate the Master Script as spoken narration for a YouTube Short.
Provide specific evidence from the script. Prefer a few high-impact issues over many minor notes.
Never claim external fact verification. Every factual risk requires human verification.
Do not rewrite the entire script. Do not inflate scores. Do not recommend manipulative clickbait.
Respect the configured brand voice and quality requirements.
Return ONLY the required structured schema."""

USER_TEMPLATE = """Project: {{project_title}} ({{project_code}})
Script: {{script_title}} ({{script_code}})

Language: {{language}}
Target duration: {{target_duration_seconds}} seconds
Target words per minute: {{target_words_per_minute}}
Estimated word count (server): {{estimated_word_count}}
Estimated duration seconds (server): {{estimated_duration_seconds}}

Brand voice: {{brand_voice}}
Quality requirements: {{quality_requirements}}

Knowledge Pack — facts:
{{knowledge_pack_facts}}

Knowledge Pack — sources:
{{knowledge_pack_sources}}

Knowledge Pack — content angle:
{{knowledge_pack_content_angle}}

Knowledge Pack — key insights:
{{knowledge_pack_key_insights}}

Discovery Brief:
{{discovery_brief}}

Story Spine:
{{story_spine}}

Master Script narration:
{{master_script}}

Context warnings:
{{context_warnings}}

Review this Master Script for educational Shorts quality. Limit priority_issues to at most {{max_priority_issues}} highest-impact items. Set verification_needed true on every factual_risk."""

PROMPT_VARIABLES = [
    "project_code",
    "project_title",
    "script_code",
    "script_title",
    "language",
    "target_duration_seconds",
    "target_words_per_minute",
    "brand_voice",
    "quality_requirements",
    "knowledge_pack_facts",
    "knowledge_pack_sources",
    "knowledge_pack_content_angle",
    "knowledge_pack_key_insights",
    "discovery_brief",
    "story_spine",
    "master_script",
    "estimated_word_count",
    "estimated_duration_seconds",
    "context_warnings",
    "max_priority_issues",
]


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code or "conflict"


class StaleReviewError(ConflictError):
    def __init__(self, message: str = "Review is stale; run a new review.") -> None:
        super().__init__(message, code="stale_review")


def ensure_quality_review_prompt(db: Session, *, owner: User) -> AiPrompt:
    existing = db.scalar(
        select(AiPrompt).where(AiPrompt.purpose == PURPOSE_QUALITY_REVIEW)
    )
    if existing is not None:
        return ai_service.get_prompt(db, existing.id)

    prompt = AiPrompt(
        name=PROMPT_NAME,
        description=(
            "Editorial quality review for Master Script narration. "
            "Advisory only — never approves content."
        ),
        purpose=PURPOSE_QUALITY_REVIEW,
        status=PROMPT_STATUS_ACTIVE,
        owner_id=owner.id,
    )
    db.add(prompt)
    db.flush()
    version = AiPromptVersion(
        prompt_id=prompt.id,
        version_number=1,
        system_prompt=SYSTEM_PROMPT,
        user_template=USER_TEMPLATE,
        variables_json=PROMPT_VARIABLES,
        status=PROMPT_VERSION_STATUS_ACTIVE,
        created_by=owner.id,
    )
    db.add(version)
    db.flush()
    prompt.active_version_id = version.id
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_CREATED,
        entity_type=ENTITY_AI_PROMPT,
        entity_id=prompt.id,
        actor_user_id=owner.id,
        metadata={"purpose": PURPOSE_QUALITY_REVIEW, "seeded": True},
    )
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_VERSION_CREATED,
        entity_type=ENTITY_AI_PROMPT_VERSION,
        entity_id=version.id,
        actor_user_id=owner.id,
        metadata={
            "prompt_id": str(prompt.id),
            "version_number": 1,
            "seeded": True,
        },
    )
    db.commit()
    return ai_service.get_prompt(db, prompt.id)


def _resolve_openai_model(db: Session, model_id: UUID | None) -> AiModel:
    ai_service.ensure_provider_catalog(db)
    if model_id is not None:
        model = ai_service.get_model(db, model_id)
    else:
        settings = ai_service.get_or_create_settings(db)
        if settings.default_model_id is None:
            openai_provider = db.scalar(
                select(AiProvider).where(AiProvider.code == PROVIDER_OPENAI)
            )
            if openai_provider is None:
                raise ValidationError("OpenAI provider is not configured.")
            model = db.scalar(
                select(AiModel).where(
                    AiModel.provider_id == openai_provider.id,
                    AiModel.is_default.is_(True),
                    AiModel.is_active.is_(True),
                )
            )
            if model is None:
                model = db.scalar(
                    select(AiModel).where(
                        AiModel.provider_id == openai_provider.id,
                        AiModel.is_active.is_(True),
                    )
                )
        else:
            model = ai_service.get_model(db, settings.default_model_id)

    if model is None:
        raise ValidationError("No active OpenAI model is configured.")
    if not model.is_active:
        raise ValidationError("Selected model is inactive.")
    provider = ai_service.get_provider(db, model.provider_id)
    if provider.code != PROVIDER_OPENAI:
        raise ValidationError("Quality review requires an OpenAI model.")
    if not provider.is_active:
        raise ValidationError("OpenAI provider is inactive.")
    return model


def _documents_by_type(script: Script) -> dict[str, ScriptDocument]:
    return {document.document_type: document for document in script.documents}


def _knowledge_pack_sections(
    db: Session, script: Script
) -> list[KnowledgePackSection]:
    if not script.knowledge_pack_id:
        return []
    return list(
        db.scalars(
            select(KnowledgePackSection)
            .where(KnowledgePackSection.knowledge_pack_id == script.knowledge_pack_id)
            .order_by(KnowledgePackSection.position.asc())
        ).all()
    )


def _section_map(sections: list[KnowledgePackSection]) -> dict[str, str]:
    by_key = {
        section.section_key: (section.content or "").strip() for section in sections
    }
    keys = ("facts", "sources", "content_angle", "key_insights")
    return {
        f"knowledge_pack_{key}": by_key.get(key, "") or "(Not provided.)"
        for key in keys
    }


def _context_warnings(docs: dict[str, ScriptDocument]) -> list[str]:
    warnings: list[str] = []
    discovery = (docs.get("discovery_brief").content if docs.get("discovery_brief") else "") or ""
    spine = (docs.get("story_spine").content if docs.get("story_spine") else "") or ""
    if not discovery.strip():
        warnings.append(
            "Discovery Brief is empty. Alignment dimensions have reduced confidence; "
            "full workflow alignment was not verified."
        )
    if not spine.strip():
        warnings.append(
            "Story Spine is empty. Structure alignment has reduced confidence; "
            "full workflow alignment was not verified."
        )
    return warnings


def _input_fingerprint(
    db: Session,
    *,
    script: Script,
    brand_voice: str,
    prompt_version_id: UUID,
) -> dict[str, Any]:
    docs = _documents_by_type(script)
    sections = _knowledge_pack_sections(db, script)
    section_hashes = {
        section.section_key: content_fingerprint(section.content or "")
        for section in sections
    }
    return {
        "master_script": content_fingerprint(
            docs["master_script"].content if "master_script" in docs else ""
        ),
        "discovery_brief": content_fingerprint(
            docs["discovery_brief"].content if "discovery_brief" in docs else ""
        ),
        "story_spine": content_fingerprint(
            docs["story_spine"].content if "story_spine" in docs else ""
        ),
        "knowledge_pack_id": (
            str(script.knowledge_pack_id) if script.knowledge_pack_id else None
        ),
        "knowledge_pack_section_hashes": section_hashes,
        "brand_voice": content_fingerprint(brand_voice),
        "review_policy": policy_fingerprint(),
        "prompt_version_id": str(prompt_version_id),
    }


def is_generation_stale(db: Session, generation: AiGeneration) -> bool:
    if not generation.script_id:
        return False
    stored = generation.input_fingerprint_json or {}
    script = db.scalar(
        select(Script)
        .options(selectinload(Script.documents))
        .where(Script.id == generation.script_id)
    )
    if script is None:
        return True
    settings = ai_service.get_or_create_settings(db)
    brand_voice = (settings.brand_voice or DEFAULT_BRAND_VOICE).strip()
    current = _input_fingerprint(
        db,
        script=script,
        brand_voice=brand_voice,
        prompt_version_id=generation.prompt_version_id,
    )
    return current != stored


def create_quality_review_job(
    db: Session,
    *,
    script_id: UUID,
    actor: User,
    model_id: UUID | None = None,
    language: str = DEFAULT_LANGUAGE,
    target_duration_seconds: int | None = None,
    target_words_per_minute: int | None = None,
    idempotency_key: str | None = None,
    execute_now: bool = True,
    ip_address: str | None = None,
    user_agent: str | None = None,
    sleep_fn=None,
) -> AiJob:
    script = script_service.get_script_for_user(db, script_id, actor)
    docs = _documents_by_type(script)
    master = docs.get("master_script")
    master_text = (master.content if master else "") or ""
    if not master_text.strip():
        raise ValidationError(
            "Master Script is empty. Write or apply a Master Script before quality review."
        )

    if idempotency_key:
        existing = db.scalar(
            select(AiJob).where(
                AiJob.requested_by == actor.id,
                AiJob.script_id == script.id,
                AiJob.purpose == PURPOSE_QUALITY_REVIEW,
                AiJob.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing

    prompt = ensure_quality_review_prompt(db, owner=actor)
    if prompt.active_version_id is None:
        raise ValidationError("Quality review prompt has no active version.")
    version = db.get(AiPromptVersion, prompt.active_version_id)
    if version is None:
        raise ValidationError("Active prompt version is missing.")

    model = _resolve_openai_model(db, model_id)
    settings = ai_service.get_or_create_settings(db)
    resolved_duration = (
        target_duration_seconds
        or settings.default_target_duration_seconds
        or DEFAULT_TARGET_DURATION_SECONDS
    )
    resolved_wpm = (
        target_words_per_minute
        or settings.default_target_words_per_minute
        or DEFAULT_TARGET_WORDS_PER_MINUTE
    )
    brand_voice = (settings.brand_voice or DEFAULT_BRAND_VOICE).strip()
    quality_requirements = (
        settings.quality_requirements or DEFAULT_QUALITY_REQUIREMENTS
    ).strip()

    sections = _knowledge_pack_sections(db, script)
    section_vars = _section_map(sections)
    warnings = _context_warnings(docs)
    words = word_count(master_text)
    est_duration = max(1, int(round((words / max(1, resolved_wpm)) * 60)))

    project: Project = script.project
    variables: dict[str, str] = {
        "project_code": project.project_code,
        "project_title": project.name,
        "script_code": script.script_code,
        "script_title": script.title,
        "language": (language or DEFAULT_LANGUAGE).strip(),
        "target_duration_seconds": str(resolved_duration),
        "target_words_per_minute": str(resolved_wpm),
        "brand_voice": brand_voice,
        "quality_requirements": quality_requirements,
        **section_vars,
        "discovery_brief": (
            (docs["discovery_brief"].content if "discovery_brief" in docs else "")
            or "(Empty.)"
        ).strip(),
        "story_spine": (
            (docs["story_spine"].content if "story_spine" in docs else "")
            or "(Empty.)"
        ).strip(),
        "master_script": master_text.strip(),
        "estimated_word_count": str(words),
        "estimated_duration_seconds": str(est_duration),
        "context_warnings": "\n".join(warnings) if warnings else "(None.)",
        "max_priority_issues": str(MAX_PRIORITY_ISSUES),
    }
    fingerprint = _input_fingerprint(
        db,
        script=script,
        brand_voice=brand_voice,
        prompt_version_id=version.id,
    )

    job = AiJob(
        status=JOB_STATUS_QUEUED,
        requested_by=actor.id,
        prompt_version_id=version.id,
        model_id=model.id,
        input_variables_json=variables,
        purpose=PURPOSE_QUALITY_REVIEW,
        project_id=project.id,
        script_id=script.id,
        document_type=QUALITY_REVIEW_DOCUMENT_TYPE,
        knowledge_pack_id=script.knowledge_pack_id,
        input_fingerprint_json=fingerprint,
        idempotency_key=idempotency_key,
    )
    db.add(job)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        if idempotency_key:
            existing = db.scalar(
                select(AiJob).where(
                    AiJob.requested_by == actor.id,
                    AiJob.script_id == script.id,
                    AiJob.purpose == PURPOSE_QUALITY_REVIEW,
                    AiJob.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                return existing
        raise ValidationError("Unable to create quality review job.") from exc

    record_audit_event(
        db,
        action=ACTION_SCRIPT_QUALITY_REVIEW_REQUESTED,
        entity_type=ENTITY_SCRIPT,
        entity_id=script.id,
        actor_user_id=actor.id,
        metadata={
            "job_id": str(job.id),
            "purpose": PURPOSE_QUALITY_REVIEW,
            "model_id": str(model.id),
            "prompt_version_id": str(version.id),
            "document_type": QUALITY_REVIEW_DOCUMENT_TYPE,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(job)

    if execute_now:
        kwargs = {
            "actor": actor,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        if sleep_fn is not None:
            kwargs["sleep_fn"] = sleep_fn
        job = execute_job(db, job.id, **kwargs)
    return job


def list_quality_reviews(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AiGeneration], int]:
    script_service.get_script_for_user(db, script_id, actor)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    filters = [
        AiGeneration.script_id == script_id,
        AiGeneration.purpose == PURPOSE_QUALITY_REVIEW,
    ]
    count_stmt = select(func.count()).select_from(AiGeneration)
    list_stmt = select(AiGeneration).order_by(AiGeneration.created_at.desc())
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)
    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return items, total


def get_latest_quality_review(
    db: Session, script_id: UUID, *, actor: User
) -> AiGeneration | None:
    items, _total = list_quality_reviews(
        db, script_id, actor=actor, page=1, page_size=1
    )
    return items[0] if items else None


def get_quality_review(
    db: Session, generation_id: UUID, *, actor: User | None = None
) -> AiGeneration:
    generation = db.get(AiGeneration, generation_id)
    if generation is None or generation.purpose != PURPOSE_QUALITY_REVIEW:
        raise NotFoundError("Quality review not found.")
    if actor is not None and generation.script_id is not None:
        script_service.get_script_for_user(db, generation.script_id, actor)
    return generation


def apply_suggestion(
    db: Session,
    *,
    script_id: UUID,
    generation_id: UUID,
    issue_id: str,
    strategy: SuggestionStrategy = "replace_excerpt",
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[ScriptDocument, AiGeneration, bool]:
    if strategy != "replace_excerpt":
        raise ValidationError("Only replace_excerpt is supported in this release.")

    script = script_service.get_script_for_user(db, script_id, actor)
    generation = get_quality_review(db, generation_id, actor=actor)
    if generation.script_id != script.id:
        raise ForbiddenError("Review does not belong to this script.")

    job = db.get(AiJob, generation.job_id)
    if job is None or job.status != JOB_STATUS_COMPLETED:
        raise ValidationError("Quality review did not complete successfully.")

    stale = is_generation_stale(db, generation)
    if stale:
        raise StaleReviewError()

    structured = generation.structured_output_json or {}
    issues = structured.get("priority_issues") or []
    issue = next(
        (item for item in issues if str(item.get("id", "")).strip() == issue_id.strip()),
        None,
    )
    if issue is None:
        raise NotFoundError("Suggestion issue not found in this review.")

    original = (issue.get("original_excerpt") or "").strip()
    rewrite = (issue.get("suggested_rewrite") or "").strip()
    if not original or not rewrite:
        raise ValidationError(
            "Issue must include a unique original excerpt and suggested rewrite."
        )

    document = _documents_by_type(script).get("master_script")
    if document is None:
        raise NotFoundError("Master Script document not found.")
    content = document.content or ""
    occurrences = content.count(original)
    if occurrences == 0:
        raise ConflictError(
            "Original excerpt not found in current Master Script.",
            code="excerpt_not_found",
        )
    if occurrences > 1:
        raise ConflictError(
            "Original excerpt appears multiple times; edit manually.",
            code="excerpt_ambiguous",
        )

    document.content = content.replace(original, rewrite, 1)
    previously = [str(item) for item in (generation.applied_sections_json or [])]
    generation.applied_sections_json = list(
        dict.fromkeys([*previously, f"issue:{issue_id}"])
    )
    generation.applied_at = datetime.now(UTC)

    record_audit_event(
        db,
        action=ACTION_SCRIPT_QUALITY_SUGGESTION_APPLIED,
        entity_type=ENTITY_SCRIPT,
        entity_id=script.id,
        actor_user_id=actor.id,
        metadata={
            "generation_id": str(generation.id),
            "job_id": str(generation.job_id),
            "issue_id": issue_id,
            "issue_category": issue.get("category"),
            "issue_severity": issue.get("severity"),
            "strategy": strategy,
            "stale_input": False,
            "prompt_version_id": str(generation.prompt_version_id),
            "model_id": str(generation.model_id),
            "overall_score": structured.get("overall_score"),
            "quality_band": structured.get("quality_band"),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(document)
    db.refresh(generation)
    document = script_service.get_document(
        db, script.id, "master_script", actor=actor
    )
    return document, generation, False


# Re-export enrichment for executor use
__all__ = [
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "StaleReviewError",
    "ValidationError",
    "apply_suggestion",
    "create_quality_review_job",
    "ensure_quality_review_prompt",
    "get_latest_quality_review",
    "get_quality_review",
    "is_generation_stale",
    "list_quality_reviews",
]
