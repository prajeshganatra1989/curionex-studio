"""Script Document AI draft queue, seed prompts, and selective apply.

Mirrors ``knowledge_pack_ai_service`` for the three Script Document drafting
purposes (Discovery Brief, Story Spine, Master Script). Jobs are queued and
optionally executed synchronously through the shared OpenAI job executor;
generations are never written directly into ``script_documents`` until an
editor explicitly applies them.
"""

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
    DEFAULT_CONFLICT_STRATEGY,
    DEFAULT_TARGET_DURATION_SECONDS,
    DEFAULT_TARGET_WORDS_PER_MINUTE,
    PURPOSE_BY_DOCUMENT_TYPE,
    PURPOSE_DISCOVERY_BRIEF,
    PURPOSE_MASTER_SCRIPT,
    PURPOSE_STORY_SPINE,
    ConflictStrategy,
    content_fingerprint,
    structured_to_plain_text,
    target_word_range,
)
from app.audit.actions import (
    ACTION_AI_PROMPT_CREATED,
    ACTION_AI_PROMPT_VERSION_CREATED,
    ACTION_SCRIPT_AI_DRAFT_APPLIED,
    ACTION_SCRIPT_AI_DRAFT_REQUESTED,
    ENTITY_AI_PROMPT,
    ENTITY_AI_PROMPT_VERSION,
    ENTITY_SCRIPT,
)
from app.editorial.content_standard_prompt import inject_content_standard_variables
from app.models.ai import (
    AiGeneration,
    AiJob,
    AiModel,
    AiPrompt,
    AiPromptVersion,
    AiProvider,
)
from app.models.knowledge_pack import KnowledgePackSection
from app.models.project import Category, Project, ProjectTag, Tag
from app.models.script import Script, ScriptDocument
from app.models.user import User
from app.scripts.catalog import DOCUMENT_TYPES
from app.services import ai_service, script_service
from app.services.audit_service import record_audit_event
from app.services.content_standard_service import (
    get_active as get_active_content_standard,
)

DEFAULT_LANGUAGE = "English"
DEFAULT_TONE = "curious, cinematic, clear"


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class ValidationError(Exception):
    pass


class ConflictError(Exception):
    def __init__(self, message: str, *, conflicts: list[str] | None = None) -> None:
        super().__init__(message)
        self.conflicts = conflicts or []


class PrerequisiteError(Exception):
    """Raised when a document draft is requested before its prior stage exists."""

    code = "missing_prerequisite"

    def __init__(self, message: str, *, missing: list[str] | None = None) -> None:
        super().__init__(message)
        self.missing = missing or []


# --- Prompt seeds -------------------------------------------------------------

_DISCOVERY_BRIEF_SYSTEM_PROMPT = """You are Curionex Studio's script development assistant creating a Discovery Brief for a short-form educational video.
A Discovery Brief defines the topic, audience, and angle before any narrative writing begins.
Ground your work in the supplied Knowledge Pack context — never invent facts beyond it.
Follow {{content_standard_label}}. Mark every claim that still needs verification.
Return ONLY the required structured schema."""

_DISCOVERY_BRIEF_USER_TEMPLATE = """Project: {{project_title}} ({{project_code}})
Description: {{project_description}}
Category: {{category}}
Tags: {{tags}}

Script: {{script_title}}
Script description: {{script_description}}

Knowledge Pack — research:
{{knowledge_pack_research}}

Knowledge Pack — facts:
{{knowledge_pack_facts}}

Knowledge Pack — sources:
{{knowledge_pack_sources}}

Knowledge Pack — audience:
{{knowledge_pack_audience}}

Knowledge Pack — content angle:
{{knowledge_pack_content_angle}}

Knowledge Pack — key insights:
{{knowledge_pack_key_insights}}

Knowledge Pack — additional context:
{{knowledge_pack_additional_context}}

Language: {{language}}
Tone: {{tone}}
Target duration: {{target_duration_seconds}} seconds

Follow the Curionex Content Standard (do not invent conflicting editorial rules):
{{content_standard}}

Produce a Discovery Brief draft for this script."""

_STORY_SPINE_SYSTEM_PROMPT = """You are Curionex Studio's script development assistant creating a Story Spine for a short-form educational video.
The Story Spine turns an approved Discovery Brief into a beat-by-beat narrative structure aligned with the Curionex Content Standard.
Stay faithful to the Discovery Brief — do not introduce new facts or claims it does not support.
Follow {{content_standard_label}}. Return ONLY the required structured schema."""

_STORY_SPINE_USER_TEMPLATE = """Project: {{project_title}} ({{project_code}})
Script: {{script_title}}

Discovery Brief:
{{discovery_brief}}

Knowledge Pack — facts:
{{knowledge_pack_facts}}

Knowledge Pack — sources:
{{knowledge_pack_sources}}

Knowledge Pack — key insights:
{{knowledge_pack_key_insights}}

Language: {{language}}
Tone: {{tone}}
Target duration: {{target_duration_seconds}} seconds
Target narration length: {{target_word_count_low}}-{{target_word_count_high}} words (target {{target_word_count_target}})

Follow the Curionex Content Standard (do not invent conflicting editorial rules):
{{content_standard}}

Produce a Story Spine draft for this script."""

_MASTER_SCRIPT_SYSTEM_PROMPT = """You are Curionex Studio's script development assistant writing the Master Script narration for a short-form educational video.
The Master Script is the final spoken narration, built strictly from the approved Discovery Brief and Story Spine.
Do not introduce new facts or claims beyond what the Discovery Brief and Story Spine support.
Write narration meant to be read aloud. Follow {{content_standard_label}}.
Aim for the target word count range for the target duration. Flag any claim that still needs verification.
Return ONLY the required structured schema."""

_MASTER_SCRIPT_USER_TEMPLATE = """Project: {{project_title}} ({{project_code}})
Script: {{script_title}}

Discovery Brief:
{{discovery_brief}}

Story Spine:
{{story_spine}}

Knowledge Pack — facts:
{{knowledge_pack_facts}}

Knowledge Pack — sources:
{{knowledge_pack_sources}}

Claims requiring verification:
{{claims_requiring_verification}}

Language: {{language}}
Tone: {{tone}}
Target duration: {{target_duration_seconds}} seconds
Target words per minute: {{target_words_per_minute}}
Target narration length: {{target_word_count_low}}-{{target_word_count_high}} words (target {{target_word_count_target}})

Follow the Curionex Content Standard (do not invent conflicting editorial rules):
{{content_standard}}

Produce the Master Script narration draft for this script."""


_PROMPT_DEFINITIONS: dict[str, dict[str, Any]] = {
    PURPOSE_DISCOVERY_BRIEF: {
        "name": "Discovery Brief Draft",
        "description": "AI-assisted first draft of a script's Discovery Brief.",
        "system_prompt": _DISCOVERY_BRIEF_SYSTEM_PROMPT,
        "user_template": _DISCOVERY_BRIEF_USER_TEMPLATE,
        "variables": [
            "project_code",
            "project_title",
            "project_description",
            "category",
            "tags",
            "knowledge_pack_research",
            "knowledge_pack_facts",
            "knowledge_pack_sources",
            "knowledge_pack_audience",
            "knowledge_pack_content_angle",
            "knowledge_pack_key_insights",
            "knowledge_pack_additional_context",
            "script_title",
            "script_description",
            "language",
            "tone",
            "target_duration_seconds",
            "content_standard",
            "content_standard_label",
        ],
    },
    PURPOSE_STORY_SPINE: {
        "name": "Story Spine Draft",
        "description": "AI-assisted first draft of a script's Story Spine.",
        "system_prompt": _STORY_SPINE_SYSTEM_PROMPT,
        "user_template": _STORY_SPINE_USER_TEMPLATE,
        "variables": [
            "project_code",
            "project_title",
            "script_title",
            "target_duration_seconds",
            "language",
            "tone",
            "discovery_brief",
            "knowledge_pack_facts",
            "knowledge_pack_sources",
            "knowledge_pack_key_insights",
            "target_word_count_low",
            "target_word_count_target",
            "target_word_count_high",
            "content_standard",
            "content_standard_label",
        ],
    },
    PURPOSE_MASTER_SCRIPT: {
        "name": "Master Script Draft",
        "description": "AI-assisted first draft of a script's Master Script narration.",
        "system_prompt": _MASTER_SCRIPT_SYSTEM_PROMPT,
        "user_template": _MASTER_SCRIPT_USER_TEMPLATE,
        "variables": [
            "project_code",
            "project_title",
            "script_title",
            "language",
            "tone",
            "target_duration_seconds",
            "target_words_per_minute",
            "discovery_brief",
            "story_spine",
            "knowledge_pack_facts",
            "knowledge_pack_sources",
            "claims_requiring_verification",
            "target_word_count_low",
            "target_word_count_target",
            "target_word_count_high",
            "content_standard",
            "content_standard_label",
        ],
    },
}


def ensure_script_draft_prompts(db: Session, *, owner: User) -> dict[str, AiPrompt]:
    """Idempotently seed the three Script Draft prompts + active versions."""
    prompts: dict[str, AiPrompt] = {}
    for purpose, definition in _PROMPT_DEFINITIONS.items():
        existing = db.scalar(select(AiPrompt).where(AiPrompt.purpose == purpose))
        if existing is not None:
            prompts[purpose] = existing
            continue

        prompt = AiPrompt(
            name=definition["name"],
            description=definition["description"],
            purpose=purpose,
            status=PROMPT_STATUS_ACTIVE,
            owner_id=owner.id,
        )
        db.add(prompt)
        db.flush()
        version = AiPromptVersion(
            prompt_id=prompt.id,
            version_number=1,
            system_prompt=definition["system_prompt"],
            user_template=definition["user_template"],
            variables_json=definition["variables"],
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
            metadata={"purpose": purpose, "seeded": True},
        )
        record_audit_event(
            db,
            action=ACTION_AI_PROMPT_VERSION_CREATED,
            entity_type=ENTITY_AI_PROMPT_VERSION,
            entity_id=version.id,
            actor_user_id=owner.id,
            metadata={"prompt_id": str(prompt.id), "version_number": 1, "seeded": True},
        )
        prompts[purpose] = prompt

    db.commit()
    return {
        purpose: ai_service.get_prompt(db, prompt.id)
        for purpose, prompt in prompts.items()
    }


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
        raise ValidationError("Script drafts require an OpenAI model.")
    if not provider.is_active:
        raise ValidationError("OpenAI provider is inactive.")
    if not model.code.strip():
        raise ValidationError("Selected model has no provider model identifier.")
    return model


# --- Context building -----------------------------------------------------


def _project_context(db: Session, project: Project) -> dict[str, str]:
    category_name = ""
    if project.category_id:
        category = db.get(Category, project.category_id)
        category_name = category.name if category else ""
    tag_names = list(
        db.scalars(
            select(Tag.name)
            .join(ProjectTag, ProjectTag.tag_id == Tag.id)
            .where(ProjectTag.project_id == project.id)
            .order_by(Tag.name.asc())
        ).all()
    )
    return {
        "project_title": project.name,
        "project_code": project.project_code,
        "project_description": project.description or "",
        "category": category_name,
        "tags": ", ".join(tag_names),
    }


def _documents_by_type(script: Script) -> dict[str, ScriptDocument]:
    return {document.document_type: document for document in script.documents}


def _knowledge_pack_sections(db: Session, script: Script) -> list[KnowledgePackSection]:
    if not script.knowledge_pack_id:
        return []
    return list(
        db.scalars(
            select(KnowledgePackSection)
            .where(KnowledgePackSection.knowledge_pack_id == script.knowledge_pack_id)
            .order_by(KnowledgePackSection.position.asc())
        ).all()
    )


def _knowledge_pack_section_map(
    sections: list[KnowledgePackSection],
) -> dict[str, str]:
    by_key = {
        section.section_key: (section.content or "").strip() for section in sections
    }
    keys = (
        "research",
        "facts",
        "sources",
        "audience",
        "content_angle",
        "key_insights",
        "additional_context",
    )
    return {
        f"knowledge_pack_{key}": by_key.get(key, "") or "(Not provided.)"
        for key in keys
    }


def _extract_claims_requiring_verification(discovery_brief: str) -> str:
    marker = "CLAIMS REQUIRING VERIFICATION"
    text = discovery_brief or ""
    upper = text.upper()
    start = upper.find(marker)
    if start < 0:
        return "(None listed in Discovery Brief.)"
    rest = text[start + len(marker) :].lstrip(":\n ")
    # Stop at the next ALL-CAPS heading line when present.
    lines = rest.splitlines()
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped
            and stripped.upper() == stripped
            and any(ch.isalpha() for ch in stripped)
            and len(stripped) < 80
        ):
            break
        collected.append(line)
    result = "\n".join(collected).strip()
    return result or "(None listed in Discovery Brief.)"


def _prerequisite_document_types(document_type: str) -> tuple[str, ...]:
    if document_type == "story_spine":
        return ("discovery_brief",)
    if document_type == "master_script":
        return ("discovery_brief", "story_spine")
    return ()


def get_document_prerequisites(script: Script) -> dict[str, dict[str, Any]]:
    """Return per-document-type readiness flags for AI drafting."""
    docs = _documents_by_type(script)

    def _is_ready(doc_type: str) -> bool:
        document = docs.get(doc_type)
        return bool(document and (document.content or "").strip())

    result: dict[str, dict[str, Any]] = {}
    for document_type in DOCUMENT_TYPES:
        required = _prerequisite_document_types(document_type)
        missing = [dep for dep in required if not _is_ready(dep)]
        result[document_type] = {"ready": not missing, "missing": missing}
    return result


def _build_variables(
    db: Session,
    *,
    project: Project,
    script: Script,
    document_type: str,
    language: str,
    tone: str,
    target_duration_seconds: int,
    target_words_per_minute: int,
) -> dict[str, str]:
    docs = _documents_by_type(script)
    sections = _knowledge_pack_sections(db, script)
    lo, target, hi = target_word_range(
        target_duration_seconds=target_duration_seconds,
        target_words_per_minute=target_words_per_minute,
    )
    discovery_text = (
        (docs["discovery_brief"].content if "discovery_brief" in docs else "") or ""
    ).strip()

    variables: dict[str, str] = {
        **_project_context(db, project),
        **_knowledge_pack_section_map(sections),
        "script_title": script.title,
        "script_description": script.description or "",
        "language": (language or DEFAULT_LANGUAGE).strip(),
        "tone": (tone or DEFAULT_TONE).strip(),
        "target_duration_seconds": str(target_duration_seconds),
        "target_words_per_minute": str(target_words_per_minute),
        "target_word_count_low": str(lo),
        "target_word_count_target": str(target),
        "target_word_count_high": str(hi),
        "claims_requiring_verification": _extract_claims_requiring_verification(
            discovery_text
        ),
    }

    for dependency in _prerequisite_document_types(document_type):
        document = docs.get(dependency)
        variables[dependency] = (document.content if document else "").strip()

    return inject_content_standard_variables(db, variables)


def _input_fingerprint(
    db: Session,
    *,
    script: Script,
    document_type: str,
) -> dict[str, Any]:
    docs = _documents_by_type(script)
    document_hashes = {
        dependency: content_fingerprint(
            docs[dependency].content if dependency in docs else ""
        )
        for dependency in _prerequisite_document_types(document_type)
    }
    sections = _knowledge_pack_sections(db, script)
    section_hashes = {
        section.section_key: content_fingerprint(section.content)
        for section in sections
    }
    standard = get_active_content_standard(db)
    settings_snapshot = {
        "content_standard_id": str(standard.id) if standard else None,
        "content_standard_version": standard.version if standard else None,
        "brand_voice": standard.brand_voice.strip() if standard else "",
        "quality_requirements": standard.quality_checklist.strip() if standard else "",
    }
    return {
        "document_type": document_type,
        "document_hashes": document_hashes,
        "knowledge_pack_id": (
            str(script.knowledge_pack_id) if script.knowledge_pack_id else None
        ),
        "knowledge_pack_section_hashes": section_hashes,
        "settings_snapshot": settings_snapshot,
    }


# --- Job creation -----------------------------------------------------------


def create_script_document_draft_job(
    db: Session,
    *,
    script_id: UUID,
    document_type: str,
    actor: User,
    model_id: UUID | None = None,
    language: str = DEFAULT_LANGUAGE,
    tone: str = DEFAULT_TONE,
    target_duration_seconds: int | None = None,
    target_words_per_minute: int | None = None,
    idempotency_key: str | None = None,
    execute_now: bool = True,
    ip_address: str | None = None,
    user_agent: str | None = None,
    sleep_fn=None,
) -> AiJob:
    script = script_service.get_script_for_user(db, script_id, actor)

    cleaned_document_type = (document_type or "").strip()
    if cleaned_document_type not in DOCUMENT_TYPES:
        raise ValidationError(f"Invalid document type: {document_type!r}")

    purpose = PURPOSE_BY_DOCUMENT_TYPE.get(cleaned_document_type)
    if purpose is None:
        raise ValidationError(
            f"No AI draft purpose configured for '{cleaned_document_type}'."
        )

    if idempotency_key:
        existing = db.scalar(
            select(AiJob).where(
                AiJob.requested_by == actor.id,
                AiJob.script_id == script.id,
                AiJob.document_type == cleaned_document_type,
                AiJob.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing

    prerequisites = get_document_prerequisites(script)
    missing = prerequisites.get(cleaned_document_type, {}).get("missing", [])
    if missing:
        raise PrerequisiteError(
            "Required prior documents are missing or empty.",
            missing=list(missing),
        )

    prompts = ensure_script_draft_prompts(db, owner=actor)
    prompt = prompts.get(purpose)
    if prompt is None or prompt.active_version_id is None:
        raise ValidationError("Script draft prompt has no active version.")
    version = db.get(AiPromptVersion, prompt.active_version_id)
    if version is None:
        raise ValidationError("Active prompt version is missing.")

    model = _resolve_openai_model(db, model_id)

    project = script.project
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

    variables = _build_variables(
        db,
        project=project,
        script=script,
        document_type=cleaned_document_type,
        language=language,
        tone=tone,
        target_duration_seconds=resolved_duration,
        target_words_per_minute=resolved_wpm,
    )
    fingerprint = _input_fingerprint(
        db, script=script, document_type=cleaned_document_type
    )

    job = AiJob(
        status=JOB_STATUS_QUEUED,
        requested_by=actor.id,
        prompt_version_id=version.id,
        model_id=model.id,
        input_variables_json=variables,
        purpose=purpose,
        project_id=project.id,
        script_id=script.id,
        document_type=cleaned_document_type,
        knowledge_pack_id=script.knowledge_pack_id,
        input_fingerprint_json=fingerprint,
        idempotency_key=idempotency_key,
    )
    db.add(job)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # Race on idempotency key — return the winner.
        if idempotency_key:
            existing = db.scalar(
                select(AiJob).where(
                    AiJob.requested_by == actor.id,
                    AiJob.script_id == script.id,
                    AiJob.document_type == cleaned_document_type,
                    AiJob.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                return existing
        raise ValidationError("Unable to create AI job.") from exc

    record_audit_event(
        db,
        action=ACTION_SCRIPT_AI_DRAFT_REQUESTED,
        entity_type=ENTITY_SCRIPT,
        entity_id=script.id,
        actor_user_id=actor.id,
        metadata={
            "job_id": str(job.id),
            "document_type": cleaned_document_type,
            "purpose": purpose,
            "model_id": str(model.id),
            "prompt_version_id": str(version.id),
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


# --- Apply generation --------------------------------------------------------


def apply_generation_to_script_document(
    db: Session,
    *,
    script_id: UUID,
    document_type: str,
    generation_id: UUID,
    conflict_strategy: ConflictStrategy = DEFAULT_CONFLICT_STRATEGY,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[ScriptDocument, AiGeneration, bool]:
    script = script_service.get_script_for_user(db, script_id, actor)

    cleaned_document_type = (document_type or "").strip()
    if cleaned_document_type not in DOCUMENT_TYPES:
        raise ValidationError(f"Invalid document type: {document_type!r}")

    purpose = PURPOSE_BY_DOCUMENT_TYPE.get(cleaned_document_type)
    if purpose is None:
        raise ValidationError(
            f"No AI draft purpose configured for '{cleaned_document_type}'."
        )

    generation = db.get(AiGeneration, generation_id)
    if generation is None:
        raise NotFoundError("AI generation not found.")
    if (
        generation.script_id != script.id
        or generation.document_type != cleaned_document_type
    ):
        raise ForbiddenError("Generation does not belong to this script document.")
    if generation.purpose != purpose:
        raise ValidationError("Generation purpose does not match document type.")
    if not generation.structured_output_json:
        raise ValidationError("Generation has no structured draft to apply.")

    job = db.get(AiJob, generation.job_id)
    if job is None or job.status != JOB_STATUS_COMPLETED:
        raise ValidationError("Generation's job did not complete successfully.")

    document = _documents_by_type(script).get(cleaned_document_type)
    if document is None:
        raise NotFoundError("Script document not found.")

    plain_text = structured_to_plain_text(purpose, generation.structured_output_json)

    existing_content = document.content or ""
    has_content = bool(existing_content.strip())
    if conflict_strategy == "reject_if_non_empty" and has_content:
        raise ConflictError(
            "Document already contains content.",
            conflicts=[cleaned_document_type],
        )

    if conflict_strategy == "append" and has_content:
        document.content = existing_content.rstrip() + "\n\n" + plain_text
    else:
        # replace, or reject_if_non_empty against empty content
        document.content = plain_text

    previously = [str(item) for item in (generation.applied_sections_json or [])]
    generation.applied_sections_json = list(
        dict.fromkeys([*previously, cleaned_document_type])
    )
    generation.applied_at = datetime.now(UTC)

    stale = is_generation_stale(db, generation)

    record_audit_event(
        db,
        action=ACTION_SCRIPT_AI_DRAFT_APPLIED,
        entity_type=ENTITY_SCRIPT,
        entity_id=script.id,
        actor_user_id=actor.id,
        metadata={
            "generation_id": str(generation.id),
            "job_id": str(generation.job_id),
            "document_type": cleaned_document_type,
            "conflict_strategy": conflict_strategy,
            "stale_input": stale,
            "prompt_version_id": str(generation.prompt_version_id),
            "model_id": str(generation.model_id),
            "tokens_total": generation.tokens_total,
            "estimated_cost_usd": generation.cost_usd,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(document)
    db.refresh(generation)

    document = script_service.get_document(
        db, script.id, cleaned_document_type, actor=actor
    )
    return document, generation, stale


def is_generation_stale(db: Session, generation: AiGeneration) -> bool:
    """Compare stored input fingerprints against the script's current state."""
    if not generation.script_id or not generation.document_type:
        return False
    stored = generation.input_fingerprint_json or {}

    script = db.scalar(
        select(Script)
        .options(selectinload(Script.documents))
        .where(Script.id == generation.script_id)
    )
    if script is None:
        return True

    current = _input_fingerprint(
        db, script=script, document_type=generation.document_type
    )
    return current != stored


def list_script_drafts(
    db: Session,
    script_id: UUID,
    *,
    document_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AiGeneration], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = [AiGeneration.script_id == script_id]
    if document_type is not None:
        cleaned = document_type.strip()
        if cleaned not in DOCUMENT_TYPES:
            raise ValidationError("Invalid document type filter.")
        filters.append(AiGeneration.document_type == cleaned)

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
