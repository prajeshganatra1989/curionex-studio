"""AI foundation domain services — providers, prompts, jobs, generations, settings.

Does NOT call live AI providers. Jobs are queued for a future worker.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.ai.constants import (
    JOB_STATUS_CANCELLED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    PROMPT_STATUS_ACTIVE,
    PROMPT_STATUS_DRAFT,
    PROMPT_VERSION_STATUS_ACTIVE,
    PROMPT_VERSION_STATUS_DRAFT,
    PROMPT_VERSION_STATUS_SUPERSEDED,
    PROVIDER_ANTHROPIC,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_GEMINI,
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    PROVIDER_OPENROUTER,
)
from app.ai.credentials import encrypt_secret
from app.ai.prompt_renderer import (
    PromptRenderError,
    extract_variables,
    render_template,
    validate_declared_variables,
)
from app.audit.actions import (
    ACTION_AI_JOB_CANCELLED,
    ACTION_AI_JOB_QUEUED,
    ACTION_AI_MODEL_UPDATED,
    ACTION_AI_PROMPT_CREATED,
    ACTION_AI_PROMPT_UPDATED,
    ACTION_AI_PROMPT_VERSION_ACTIVATED,
    ACTION_AI_PROMPT_VERSION_CREATED,
    ACTION_AI_PROVIDER_CREDENTIALS_CLEARED,
    ACTION_AI_PROVIDER_CREDENTIALS_SET,
    ACTION_AI_PROVIDER_UPDATED,
    ACTION_AI_SETTINGS_CHANGED,
    ENTITY_AI_JOB,
    ENTITY_AI_MODEL,
    ENTITY_AI_PROMPT,
    ENTITY_AI_PROMPT_VERSION,
    ENTITY_AI_PROVIDER,
    ENTITY_AI_SETTINGS,
)
from app.models.ai import (
    AiGeneration,
    AiJob,
    AiModel,
    AiPrompt,
    AiPromptVersion,
    AiProvider,
    AiSettings,
)
from app.models.user import User
from app.schemas.ai import (
    AiJobCreate,
    AiModelUpdate,
    AiPromptCreate,
    AiPromptUpdate,
    AiPromptVersionCreate,
    AiProviderCredentials,
    AiProviderUpdate,
    AiSettingsUpdate,
)
from app.services.audit_service import record_audit_event

# Catalog seeds — (provider_code, provider_name, models[])
_PROVIDER_SEED: list[tuple[str, str, list[dict]]] = [
    (
        PROVIDER_OPENAI,
        "OpenAI",
        [
            {
                "code": "gpt-4o",
                "name": "GPT-4o",
                "context_window": 128000,
                "supports_reasoning": False,
                "supports_streaming": True,
                "is_default": True,
                "pricing_input_per_1k": 0.0025,
                "pricing_output_per_1k": 0.01,
            },
            {
                "code": "gpt-4.1",
                "name": "GPT-4.1",
                "context_window": 1047576,
                "supports_reasoning": False,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": 0.002,
                "pricing_output_per_1k": 0.008,
            },
        ],
    ),
    (
        PROVIDER_ANTHROPIC,
        "Anthropic",
        [
            {
                "code": "claude-sonnet-4",
                "name": "Claude Sonnet 4",
                "context_window": 200000,
                "supports_reasoning": True,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": 0.003,
                "pricing_output_per_1k": 0.015,
            },
        ],
    ),
    (
        PROVIDER_GEMINI,
        "Google Gemini",
        [
            {
                "code": "gemini-2.0-pro",
                "name": "Gemini 2.0 Pro",
                "context_window": 1000000,
                "supports_reasoning": True,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": 0.00125,
                "pricing_output_per_1k": 0.005,
            },
        ],
    ),
    (
        PROVIDER_OPENROUTER,
        "OpenRouter",
        [
            {
                "code": "openrouter/auto",
                "name": "OpenRouter Auto",
                "context_window": 128000,
                "supports_reasoning": False,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": None,
                "pricing_output_per_1k": None,
            },
        ],
    ),
    (
        PROVIDER_AZURE_OPENAI,
        "Azure OpenAI",
        [
            {
                "code": "gpt-4o",
                "name": "Azure GPT-4o",
                "context_window": 128000,
                "supports_reasoning": False,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": 0.0025,
                "pricing_output_per_1k": 0.01,
            },
        ],
    ),
    (
        PROVIDER_OLLAMA,
        "Ollama",
        [
            {
                "code": "llama3.2",
                "name": "Llama 3.2",
                "context_window": 128000,
                "supports_reasoning": False,
                "supports_streaming": True,
                "is_default": False,
                "pricing_input_per_1k": 0.0,
                "pricing_output_per_1k": 0.0,
            },
        ],
    ),
]


class NotFoundError(Exception):
    """Raised when an AI entity cannot be found."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


class ConflictError(Exception):
    """Raised for state conflicts."""


def ensure_provider_catalog(db: Session) -> None:
    """Idempotently seed built-in providers and models."""
    for code, name, models in _PROVIDER_SEED:
        provider = db.scalar(select(AiProvider).where(AiProvider.code == code))
        if provider is None:
            provider = AiProvider(code=code, name=name, is_active=True)
            db.add(provider)
            db.flush()
        for model_spec in models:
            existing = db.scalar(
                select(AiModel).where(
                    AiModel.provider_id == provider.id,
                    AiModel.code == model_spec["code"],
                )
            )
            if existing is not None:
                continue
            db.add(
                AiModel(
                    provider_id=provider.id,
                    code=model_spec["code"],
                    name=model_spec["name"],
                    context_window=model_spec.get("context_window"),
                    supports_reasoning=bool(model_spec.get("supports_reasoning")),
                    supports_streaming=bool(model_spec.get("supports_streaming")),
                    is_active=True,
                    is_default=bool(model_spec.get("is_default")),
                    pricing_input_per_1k=model_spec.get("pricing_input_per_1k"),
                    pricing_output_per_1k=model_spec.get("pricing_output_per_1k"),
                )
            )
    db.flush()


def provider_has_credentials(provider: AiProvider) -> bool:
    return bool(provider.encrypted_api_key)


def list_providers(db: Session) -> list[AiProvider]:
    ensure_provider_catalog(db)
    return list(db.scalars(select(AiProvider).order_by(AiProvider.name.asc())).all())


def get_provider(db: Session, provider_id: UUID) -> AiProvider:
    ensure_provider_catalog(db)
    provider = db.get(AiProvider, provider_id)
    if provider is None:
        raise NotFoundError("AI provider not found.")
    return provider


def update_provider(
    db: Session,
    provider_id: UUID,
    payload: AiProviderUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiProvider:
    provider = get_provider(db, provider_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return provider
    if "is_active" in data and data["is_active"] is not None:
        provider.is_active = data["is_active"]
    if "base_url" in data:
        provider.base_url = data["base_url"]
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROVIDER_UPDATED,
        entity_type=ENTITY_AI_PROVIDER,
        entity_id=provider.id,
        actor_user_id=actor.id,
        metadata={"fields": sorted(data.keys()), "code": provider.code},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(provider)
    return provider


def set_provider_credentials(
    db: Session,
    provider_id: UUID,
    payload: AiProviderCredentials,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiProvider:
    provider = get_provider(db, provider_id)
    # Encrypt before assign — plaintext never persisted.
    provider.encrypted_api_key = encrypt_secret(payload.api_key)
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROVIDER_CREDENTIALS_SET,
        entity_type=ENTITY_AI_PROVIDER,
        entity_id=provider.id,
        actor_user_id=actor.id,
        metadata={"code": provider.code, "has_credentials": True},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(provider)
    return provider


def clear_provider_credentials(
    db: Session,
    provider_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiProvider:
    provider = get_provider(db, provider_id)
    provider.encrypted_api_key = None
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROVIDER_CREDENTIALS_CLEARED,
        entity_type=ENTITY_AI_PROVIDER,
        entity_id=provider.id,
        actor_user_id=actor.id,
        metadata={"code": provider.code, "has_credentials": False},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(provider)
    return provider


def list_models(db: Session, *, provider_id: UUID | None = None) -> list[AiModel]:
    ensure_provider_catalog(db)
    stmt = select(AiModel).order_by(AiModel.name.asc())
    if provider_id is not None:
        stmt = stmt.where(AiModel.provider_id == provider_id)
    return list(db.scalars(stmt).all())


def get_model(db: Session, model_id: UUID) -> AiModel:
    ensure_provider_catalog(db)
    model = db.get(AiModel, model_id)
    if model is None:
        raise NotFoundError("AI model not found.")
    return model


def update_model(
    db: Session,
    model_id: UUID,
    payload: AiModelUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiModel:
    model = get_model(db, model_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return model
    if data.get("is_default") is True:
        siblings = db.scalars(
            select(AiModel).where(AiModel.provider_id == model.provider_id)
        ).all()
        for sibling in siblings:
            sibling.is_default = sibling.id == model.id
    if "is_active" in data and data["is_active"] is not None:
        model.is_active = data["is_active"]
    if "is_default" in data and data["is_default"] is not None:
        model.is_default = data["is_default"]
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_MODEL_UPDATED,
        entity_type=ENTITY_AI_MODEL,
        entity_id=model.id,
        actor_user_id=actor.id,
        metadata={"fields": sorted(data.keys()), "code": model.code},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(model)
    return model


def _version_variables(version: AiPromptVersion) -> list[str]:
    raw = version.variables_json or []
    return [str(item) for item in raw]


def _load_prompt(db: Session, prompt_id: UUID) -> AiPrompt:
    prompt = db.scalar(
        select(AiPrompt)
        .where(AiPrompt.id == prompt_id)
        .options(selectinload(AiPrompt.versions))
    )
    if prompt is None:
        raise NotFoundError("AI prompt not found.")
    return prompt


def get_active_version(db: Session, prompt: AiPrompt) -> AiPromptVersion | None:
    if prompt.active_version_id is None:
        return None
    return db.get(AiPromptVersion, prompt.active_version_id)


def list_prompts(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[AiPrompt], int]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    stmt = select(AiPrompt)
    count_stmt = select(func.count()).select_from(AiPrompt)
    if status:
        stmt = stmt.where(AiPrompt.status == status)
        count_stmt = count_stmt.where(AiPrompt.status == status)
    if search:
        pattern = f"%{search.strip()}%"
        filt = or_(AiPrompt.name.ilike(pattern), AiPrompt.purpose.ilike(pattern))
        stmt = stmt.where(filt)
        count_stmt = count_stmt.where(filt)
    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(AiPrompt.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def create_prompt(
    db: Session,
    payload: AiPromptCreate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiPrompt:
    purpose = payload.purpose or "general"
    try:
        validate_declared_variables(
            payload.variables, payload.system_prompt, payload.user_template
        )
    except PromptRenderError as exc:
        raise ValidationError(str(exc)) from exc

    # Merge declared + extracted so templates stay consistent.
    merged = list(
        dict.fromkeys(
            payload.variables
            + extract_variables(payload.system_prompt, payload.user_template)
        )
    )

    prompt = AiPrompt(
        name=payload.name,
        description=payload.description,
        purpose=purpose,
        status=PROMPT_STATUS_DRAFT,
        owner_id=actor.id,
    )
    db.add(prompt)
    db.flush()

    version = AiPromptVersion(
        prompt_id=prompt.id,
        version_number=1,
        system_prompt=payload.system_prompt,
        user_template=payload.user_template,
        variables_json=merged,
        status=PROMPT_VERSION_STATUS_ACTIVE,
        created_by=actor.id,
    )
    db.add(version)
    db.flush()
    prompt.active_version_id = version.id
    prompt.status = PROMPT_STATUS_ACTIVE
    db.flush()

    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_CREATED,
        entity_type=ENTITY_AI_PROMPT,
        entity_id=prompt.id,
        actor_user_id=actor.id,
        metadata={"name": prompt.name, "purpose": prompt.purpose},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_VERSION_CREATED,
        entity_type=ENTITY_AI_PROMPT_VERSION,
        entity_id=version.id,
        actor_user_id=actor.id,
        metadata={"prompt_id": str(prompt.id), "version_number": 1},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return _load_prompt(db, prompt.id)


def get_prompt(db: Session, prompt_id: UUID) -> AiPrompt:
    return _load_prompt(db, prompt_id)


def update_prompt(
    db: Session,
    prompt_id: UUID,
    payload: AiPromptUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiPrompt:
    prompt = _load_prompt(db, prompt_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return prompt
    if "name" in data and data["name"] is not None:
        prompt.name = data["name"]
    if "description" in data:
        prompt.description = data["description"]
    if "purpose" in data and data["purpose"] is not None:
        prompt.purpose = data["purpose"]
    if "status" in data and data["status"] is not None:
        prompt.status = data["status"]
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_UPDATED,
        entity_type=ENTITY_AI_PROMPT,
        entity_id=prompt.id,
        actor_user_id=actor.id,
        metadata={"fields": sorted(data.keys())},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return _load_prompt(db, prompt.id)


def list_prompt_versions(db: Session, prompt_id: UUID) -> list[AiPromptVersion]:
    _load_prompt(db, prompt_id)
    return list(
        db.scalars(
            select(AiPromptVersion)
            .where(AiPromptVersion.prompt_id == prompt_id)
            .order_by(AiPromptVersion.version_number.desc())
        ).all()
    )


def create_prompt_version(
    db: Session,
    prompt_id: UUID,
    payload: AiPromptVersionCreate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiPromptVersion:
    prompt = _load_prompt(db, prompt_id)
    try:
        validate_declared_variables(
            payload.variables, payload.system_prompt, payload.user_template
        )
    except PromptRenderError as exc:
        raise ValidationError(str(exc)) from exc

    merged = list(
        dict.fromkeys(
            payload.variables
            + extract_variables(payload.system_prompt, payload.user_template)
        )
    )
    max_num = db.scalar(
        select(func.max(AiPromptVersion.version_number)).where(
            AiPromptVersion.prompt_id == prompt.id
        )
    )
    next_num = int(max_num or 0) + 1
    version = AiPromptVersion(
        prompt_id=prompt.id,
        version_number=next_num,
        system_prompt=payload.system_prompt,
        user_template=payload.user_template,
        variables_json=merged,
        status=PROMPT_VERSION_STATUS_DRAFT,
        created_by=actor.id,
    )
    db.add(version)
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_VERSION_CREATED,
        entity_type=ENTITY_AI_PROMPT_VERSION,
        entity_id=version.id,
        actor_user_id=actor.id,
        metadata={
            "prompt_id": str(prompt.id),
            "version_number": next_num,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(version)
    return version


def activate_prompt_version(
    db: Session,
    prompt_id: UUID,
    version_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiPrompt:
    prompt = _load_prompt(db, prompt_id)
    version = db.get(AiPromptVersion, version_id)
    if version is None or version.prompt_id != prompt.id:
        raise NotFoundError("Prompt version not found.")

    for existing in prompt.versions:
        if existing.id == version.id:
            existing.status = PROMPT_VERSION_STATUS_ACTIVE
        elif existing.status == PROMPT_VERSION_STATUS_ACTIVE:
            existing.status = PROMPT_VERSION_STATUS_SUPERSEDED

    prompt.active_version_id = version.id
    if prompt.status == PROMPT_STATUS_DRAFT:
        prompt.status = PROMPT_STATUS_ACTIVE
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_PROMPT_VERSION_ACTIVATED,
        entity_type=ENTITY_AI_PROMPT_VERSION,
        entity_id=version.id,
        actor_user_id=actor.id,
        metadata={
            "prompt_id": str(prompt.id),
            "version_number": version.version_number,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return _load_prompt(db, prompt.id)


def create_job(
    db: Session,
    payload: AiJobCreate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiJob:
    """Queue an AI job without calling any provider.

    Validates prompt version, model, and input variables; renders templates to
    prove the pipeline; leaves the job in ``queued`` for a future worker.
    """
    ensure_provider_catalog(db)
    prompt = _load_prompt(db, payload.prompt_id)
    if prompt.active_version_id is None:
        raise ValidationError("Prompt has no active version.")
    version = db.get(AiPromptVersion, prompt.active_version_id)
    if version is None:
        raise ValidationError("Active prompt version is missing.")
    if prompt.status == "archived":
        raise ValidationError("Cannot queue jobs for an archived prompt.")

    model = get_model(db, payload.model_id)
    if not model.is_active:
        raise ValidationError("Selected model is inactive.")
    provider = get_provider(db, model.provider_id)
    if not provider.is_active:
        raise ValidationError("Selected provider is inactive.")

    variables = {str(k): str(v) for k, v in (payload.input_variables or {}).items()}
    declared = _version_variables(version)
    missing = [name for name in declared if name not in variables]
    if missing:
        raise ValidationError("Missing input variables: " + ", ".join(sorted(missing)))
    try:
        # Render to validate — results are not stored as generated content.
        render_template(version.system_prompt, variables)
        render_template(version.user_template, variables)
    except PromptRenderError as exc:
        raise ValidationError(str(exc)) from exc

    job = AiJob(
        status=JOB_STATUS_QUEUED,
        requested_by=actor.id,
        prompt_version_id=version.id,
        model_id=model.id,
        input_variables_json=variables,
    )
    db.add(job)
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_JOB_QUEUED,
        entity_type=ENTITY_AI_JOB,
        entity_id=job.id,
        actor_user_id=actor.id,
        metadata={
            "prompt_id": str(prompt.id),
            "prompt_version_id": str(version.id),
            "model_id": str(model.id),
            "provider_code": provider.code,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(job)
    return job


def list_jobs(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[AiJob], int]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    stmt = select(AiJob)
    count_stmt = select(func.count()).select_from(AiJob)
    if status:
        stmt = stmt.where(AiJob.status == status)
        count_stmt = count_stmt.where(AiJob.status == status)
    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(
            stmt.order_by(AiJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def get_job(db: Session, job_id: UUID) -> AiJob:
    job = db.get(AiJob, job_id)
    if job is None:
        raise NotFoundError("AI job not found.")
    return job


def cancel_job(
    db: Session,
    job_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiJob:
    job = get_job(db, job_id)
    if job.status not in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}:
        raise ConflictError("Only queued or running jobs can be cancelled.")
    job.status = JOB_STATUS_CANCELLED
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_JOB_CANCELLED,
        entity_type=ENTITY_AI_JOB,
        entity_id=job.id,
        actor_user_id=actor.id,
        metadata={"previous_cancellable": True},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(job)
    return job


def list_generations(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AiGeneration], int]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    total = int(db.scalar(select(func.count()).select_from(AiGeneration)) or 0)
    items = list(
        db.scalars(
            select(AiGeneration)
            .order_by(AiGeneration.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return items, total


def get_generation(db: Session, generation_id: UUID) -> AiGeneration:
    generation = db.get(AiGeneration, generation_id)
    if generation is None:
        raise NotFoundError("AI generation not found.")
    return generation


def get_or_create_settings(db: Session) -> AiSettings:
    ensure_provider_catalog(db)
    row = db.scalar(select(AiSettings).limit(1))
    if row is None:
        row = AiSettings()
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def update_settings(
    db: Session,
    payload: AiSettingsUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AiSettings:
    settings_row = get_or_create_settings(db)
    data = payload.model_dump(exclude_unset=True)
    if "default_model_id" in data:
        model_id = data["default_model_id"]
        if model_id is not None:
            get_model(db, model_id)
        settings_row.default_model_id = model_id
    if "default_temperature" in data and data["default_temperature"] is not None:
        settings_row.default_temperature = data["default_temperature"]
    if "default_max_tokens" in data and data["default_max_tokens"] is not None:
        settings_row.default_max_tokens = data["default_max_tokens"]
    settings_row.updated_by = actor.id
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_SETTINGS_CHANGED,
        entity_type=ENTITY_AI_SETTINGS,
        entity_id=settings_row.id,
        actor_user_id=actor.id,
        metadata={"fields": sorted(data.keys())},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(settings_row)
    return settings_row
