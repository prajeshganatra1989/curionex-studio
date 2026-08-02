"""Knowledge Pack AI draft queue, seed prompt, and selective apply."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.constants import (
    JOB_STATUS_QUEUED,
    PROMPT_STATUS_ACTIVE,
    PROMPT_VERSION_STATUS_ACTIVE,
    PROVIDER_OPENAI,
)
from app.ai.job_executor import execute_job
from app.ai.knowledge_pack_draft import (
    APPLYABLE_SECTIONS,
    DEFAULT_CONFLICT_STRATEGY,
    PURPOSE_KNOWLEDGE_PACK_DRAFT,
    ConflictStrategy,
    draft_section_to_plain_text,
    parse_knowledge_pack_draft,
)
from app.audit.actions import (
    ACTION_AI_JOB_QUEUED,
    ACTION_AI_PROMPT_CREATED,
    ACTION_AI_PROMPT_VERSION_CREATED,
    ACTION_KNOWLEDGE_PACK_AI_DRAFT_APPLIED,
    ENTITY_AI_JOB,
    ENTITY_AI_PROMPT,
    ENTITY_AI_PROMPT_VERSION,
    ENTITY_KNOWLEDGE_PACK,
)
from app.models.ai import (
    AiGeneration,
    AiJob,
    AiModel,
    AiPrompt,
    AiPromptVersion,
    AiProvider,
)
from app.models.knowledge_pack import KnowledgePack, KnowledgePackSection
from app.models.project import Category, Project, ProjectTag, Tag
from app.models.user import User
from app.services import ai_service, knowledge_pack_service
from app.services.audit_service import record_audit_event

PROMPT_NAME = "Knowledge Pack Draft"

SYSTEM_PROMPT = """You are Curionex Studio's research drafting assistant.
Create a useful research starting point for an educational short-form video.
Separate claims from interpretation. Avoid fabricated certainty and sensationalism.
Mark every source as unverified — never claim scientific or factual verification.
Identify ambiguity and flag risky or unsupported claims in warnings.
Return ONLY the required structured schema. This is a research draft, not a fact-check."""

USER_TEMPLATE = """Project: {{project_title}}
Description: {{project_description}}
Category: {{category}}
Tags: {{tags}}
Topic: {{topic}}
Target audience: {{target_audience}}
Language: {{language}}
Desired depth: {{desired_depth}}

Produce a Knowledge Pack draft for this topic."""


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


def ensure_knowledge_pack_draft_prompt(db: Session, *, owner: User) -> AiPrompt:
    """Idempotently seed the Knowledge Pack Draft prompt + active version."""
    existing = db.scalar(
        select(AiPrompt).where(AiPrompt.purpose == PURPOSE_KNOWLEDGE_PACK_DRAFT)
    )
    if existing is not None:
        return existing

    variables = [
        "topic",
        "project_title",
        "project_description",
        "category",
        "tags",
        "target_audience",
        "language",
        "desired_depth",
    ]
    prompt = AiPrompt(
        name=PROMPT_NAME,
        description=(
            "Structured research draft for Knowledge Packs. "
            "Sources are always unverified and require human review."
        ),
        purpose=PURPOSE_KNOWLEDGE_PACK_DRAFT,
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
        variables_json=variables,
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
        metadata={"purpose": PURPOSE_KNOWLEDGE_PACK_DRAFT, "seeded": True},
    )
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_VERSION_CREATED,
        entity_type=ENTITY_AI_PROMPT_VERSION,
        entity_id=version.id,
        actor_user_id=owner.id,
        metadata={"prompt_id": str(prompt.id), "version_number": 1, "seeded": True},
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
        raise ValidationError("Knowledge Pack drafts require an OpenAI model.")
    if not provider.is_active:
        raise ValidationError("OpenAI provider is inactive.")
    if not model.code.strip():
        raise ValidationError("Selected model has no provider model identifier.")
    return model


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
        "project_description": project.description or "",
        "category": category_name,
        "tags": ", ".join(tag_names),
        "topic": project.name,
    }


def create_knowledge_pack_draft_job(
    db: Session,
    *,
    project_id: UUID,
    knowledge_pack_id: UUID,
    actor: User,
    model_id: UUID | None = None,
    target_audience: str = "general learners",
    language: str = "en",
    desired_depth: str = "standard",
    idempotency_key: str | None = None,
    execute_now: bool = True,
    ip_address: str | None = None,
    user_agent: str | None = None,
    sleep_fn=None,
) -> AiJob:
    pack = knowledge_pack_service.get_knowledge_pack_for_user(
        db, knowledge_pack_id, actor
    )
    if pack.project_id != project_id:
        raise ValidationError("Knowledge Pack does not belong to this project.")
    project = knowledge_pack_service.assert_project_access(db, project_id, actor)

    if idempotency_key:
        existing = db.scalar(
            select(AiJob).where(
                AiJob.requested_by == actor.id,
                AiJob.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing

    prompt = ensure_knowledge_pack_draft_prompt(db, owner=actor)
    if prompt.active_version_id is None:
        raise ValidationError("Knowledge Pack Draft prompt has no active version.")
    version = db.get(AiPromptVersion, prompt.active_version_id)
    if version is None:
        raise ValidationError("Active prompt version is missing.")

    model = _resolve_openai_model(db, model_id)
    context = _project_context(db, project)
    variables = {
        **context,
        "target_audience": (target_audience or "general learners").strip(),
        "language": (language or "en").strip(),
        "desired_depth": (desired_depth or "standard").strip(),
    }

    job = AiJob(
        status=JOB_STATUS_QUEUED,
        requested_by=actor.id,
        prompt_version_id=version.id,
        model_id=model.id,
        input_variables_json=variables,
        purpose=PURPOSE_KNOWLEDGE_PACK_DRAFT,
        knowledge_pack_id=pack.id,
        project_id=project.id,
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
                    AiJob.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                return existing
        raise ValidationError("Unable to create AI job.") from exc

    record_audit_event(
        db,
        action=ACTION_AI_JOB_QUEUED,
        entity_type=ENTITY_AI_JOB,
        entity_id=job.id,
        actor_user_id=actor.id,
        metadata={
            "purpose": PURPOSE_KNOWLEDGE_PACK_DRAFT,
            "knowledge_pack_id": str(pack.id),
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


def apply_generation_to_knowledge_pack(
    db: Session,
    *,
    knowledge_pack_id: UUID,
    generation_id: UUID,
    sections: list[str],
    conflict_strategy: ConflictStrategy = DEFAULT_CONFLICT_STRATEGY,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[KnowledgePack, AiGeneration, list[str]]:
    pack = knowledge_pack_service.get_knowledge_pack_for_user(
        db, knowledge_pack_id, actor
    )
    generation = db.get(AiGeneration, generation_id)
    if generation is None:
        raise NotFoundError("AI generation not found.")
    if generation.knowledge_pack_id != pack.id:
        raise ForbiddenError("Generation does not belong to this Knowledge Pack.")
    if generation.project_id and generation.project_id != pack.project_id:
        raise ForbiddenError("Generation project does not match Knowledge Pack.")
    if not generation.structured_output_json:
        raise ValidationError("Generation has no structured draft to apply.")

    selected = []
    for key in sections:
        cleaned = key.strip()
        if cleaned not in APPLYABLE_SECTIONS:
            raise ValidationError(f"Invalid section key: {cleaned}")
        if cleaned not in selected:
            selected.append(cleaned)
    if not selected:
        raise ValidationError("Select at least one section to apply.")

    draft = parse_knowledge_pack_draft(generation.structured_output_json)
    section_rows = {
        row.section_key: row
        for row in db.scalars(
            select(KnowledgePackSection).where(
                KnowledgePackSection.knowledge_pack_id == pack.id
            )
        ).all()
    }

    conflicts: list[str] = []
    for key in selected:
        row = section_rows.get(key)
        if row is None:
            raise ValidationError(f"Knowledge Pack is missing section: {key}")
        if (row.content or "").strip():
            conflicts.append(key)

    if conflict_strategy == "reject_if_non_empty" and conflicts:
        raise ConflictError(
            "Selected sections already contain content.",
            conflicts=conflicts,
        )

    applied: list[str] = []
    for key in selected:
        row = section_rows[key]
        plain = draft_section_to_plain_text(key, draft)
        existing = row.content or ""
        if conflict_strategy == "append_selected" and existing.strip():
            row.content = existing.rstrip() + "\n\n" + plain
        else:
            # replace_selected or empty reject path
            row.content = plain
        applied.append(key)

    previously = [str(item) for item in (generation.applied_sections_json or [])]
    merged = list(dict.fromkeys([*previously, *applied]))
    generation.applied_sections_json = merged
    generation.applied_at = datetime.now(UTC)

    record_audit_event(
        db,
        action=ACTION_KNOWLEDGE_PACK_AI_DRAFT_APPLIED,
        entity_type=ENTITY_KNOWLEDGE_PACK,
        entity_id=pack.id,
        actor_user_id=actor.id,
        metadata={
            "generation_id": str(generation.id),
            "job_id": str(generation.job_id),
            "sections": applied,
            "conflict_strategy": conflict_strategy,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    pack = knowledge_pack_service.get_knowledge_pack(db, pack.id)
    db.refresh(generation)
    return pack, generation, applied
