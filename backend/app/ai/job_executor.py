"""Synchronous AI job execution with retries (OpenAI live path)."""

from __future__ import annotations

import random
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.constants import (
    JOB_STATUS_CANCELLED,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    PROVIDER_OPENAI,
)
from app.ai.cost import estimate_cost_usd
from app.ai.credentials import CredentialEncryptionError, decrypt_secret
from app.ai.errors import (
    AIDomainError,
    ProviderConfigurationError,
    StructuredOutputError,
)
from app.ai.knowledge_pack_draft import (
    PURPOSE_KNOWLEDGE_PACK_DRAFT,
    knowledge_pack_draft_json_schema,
    parse_knowledge_pack_draft,
)
from app.ai.prompt_renderer import PromptRenderError, render_template
from app.ai.providers import get_provider
from app.ai.providers.base import GenerationRequest, ProviderNotImplementedError
from app.ai.retry import decide_retry
from app.audit.actions import (
    ACTION_AI_JOB_COMPLETED,
    ACTION_AI_JOB_FAILED,
    ACTION_AI_JOB_STARTED,
    ENTITY_AI_JOB,
)
from app.models.ai import (
    AiGeneration,
    AiGenerationLog,
    AiJob,
    AiModel,
    AiPromptVersion,
    AiProvider,
    AiSettings,
)
from app.models.user import User
from app.services.audit_service import record_audit_event


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _backoff_seconds(attempt: int) -> float:
    """Bounded exponential backoff with jitter (attempt is 1-based)."""
    base = min(8.0, 0.5 * (2 ** (attempt - 1)))
    return base + random.uniform(0, 0.25)


def _model_supports_structured(model: AiModel) -> bool:
    meta = model.metadata_json or {}
    if "supports_structured_output" in meta:
        return bool(meta["supports_structured_output"])
    return True


def _model_supports_temperature(model: AiModel) -> bool:
    meta = model.metadata_json or {}
    if "supports_temperature" in meta:
        return bool(meta["supports_temperature"])
    return True


def execute_job(
    db: Session,
    job_id: UUID,
    *,
    actor: User | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    sleep_fn=time.sleep,
) -> AiJob:
    """Run a queued job synchronously through the provider registry.

    Retries transient provider errors using ``decide_retry`` and backoff.
    """
    job = db.get(AiJob, job_id)
    if job is None:
        raise LookupError("AI job not found.")

    if job.status == JOB_STATUS_CANCELLED or job.cancel_requested:
        job.status = JOB_STATUS_CANCELLED
        job.finished_at = _utcnow()
        db.commit()
        db.refresh(job)
        return job

    if job.status not in {JOB_STATUS_QUEUED, JOB_STATUS_FAILED}:
        return job

    version = db.get(AiPromptVersion, job.prompt_version_id)
    model = db.get(AiModel, job.model_id)
    if version is None or model is None:
        return _fail_job(
            db,
            job,
            "Job references a missing prompt version or model.",
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    provider_row = db.get(AiProvider, model.provider_id)
    if provider_row is None or not provider_row.is_active or not model.is_active:
        return _fail_job(
            db,
            job,
            "Selected provider or model is inactive.",
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    settings_row = db.scalar(select(AiSettings).limit(1))
    temperature = settings_row.default_temperature if settings_row else 0.7
    max_tokens = settings_row.default_max_tokens if settings_row else 2048

    variables = dict(job.input_variables_json or {})
    try:
        system_prompt = render_template(version.system_prompt, variables)
        user_prompt = render_template(version.user_template, variables)
    except PromptRenderError as exc:
        return _fail_job(
            db,
            job,
            str(exc),
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    try:
        api_key = (
            decrypt_secret(provider_row.encrypted_api_key)
            if provider_row.encrypted_api_key
            else None
        )
    except CredentialEncryptionError as exc:
        return _fail_job(
            db,
            job,
            str(exc),
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    if provider_row.code == PROVIDER_OPENAI and not api_key:
        return _fail_job(
            db,
            job,
            "OpenAI credentials are not configured. Add them in AI Settings.",
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    schema = None
    schema_name = None
    if job.purpose == PURPOSE_KNOWLEDGE_PACK_DRAFT:
        schema = knowledge_pack_draft_json_schema()
        schema_name = "knowledge_pack_draft"

    request = GenerationRequest(
        model_code=model.code,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        response_json_schema=schema,
        response_schema_name=schema_name,
        supports_structured_output=_model_supports_structured(model),
        supports_temperature=_model_supports_temperature(model),
        api_key=api_key,
        base_url=provider_row.base_url,
    )

    job.status = JOB_STATUS_RUNNING
    job.started_at = _utcnow()
    job.error_message = None
    db.flush()
    record_audit_event(
        db,
        action=ACTION_AI_JOB_STARTED,
        entity_type=ENTITY_AI_JOB,
        entity_id=job.id,
        actor_user_id=actor.id if actor else job.requested_by,
        metadata={"purpose": job.purpose, "model_id": str(model.id)},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(job)

    adapter = get_provider(provider_row.code)
    last_error: Exception | None = None

    while True:
        db.refresh(job)
        if job.cancel_requested:
            job.status = JOB_STATUS_CANCELLED
            job.finished_at = _utcnow()
            if job.started_at:
                job.duration_ms = int(
                    (job.finished_at - job.started_at).total_seconds() * 1000
                )
            db.commit()
            db.refresh(job)
            return job

        try:
            result = adapter.generate(request)
            structured = result.structured_output
            if schema is not None:
                if structured is None:
                    raise StructuredOutputError(
                        "Provider returned no structured output."
                    )
                # Force verify status + schema validation.
                draft = parse_knowledge_pack_draft(structured)
                structured = draft.model_dump()

            finished = _utcnow()
            cost = estimate_cost_usd(
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                pricing_input_per_1k=model.pricing_input_per_1k,
                pricing_output_per_1k=model.pricing_output_per_1k,
            )
            generation = AiGeneration(
                job_id=job.id,
                prompt_version_id=version.id,
                model_id=model.id,
                provider_id=provider_row.id,
                input_variables_json=variables,
                output_text=result.output_text,
                structured_output_json=structured,
                purpose=job.purpose,
                knowledge_pack_id=job.knowledge_pack_id,
                project_id=job.project_id,
                tokens_input=result.tokens_input,
                tokens_output=result.tokens_output,
                tokens_total=result.tokens_total,
                cost_usd=cost,
                latency_ms=result.latency_ms,
                provider_request_id=result.provider_request_id,
                model_identifier=result.model_identifier,
                reasoning_metadata_json=result.reasoning_metadata,
                temperature=temperature,
            )
            db.add(generation)
            db.flush()
            db.add(
                AiGenerationLog(
                    generation_id=generation.id,
                    level="info",
                    message="Generation completed.",
                    details_json={
                        "provider_request_id": result.provider_request_id,
                        "tokens_total": result.tokens_total,
                    },
                )
            )
            job.status = JOB_STATUS_COMPLETED
            job.finished_at = finished
            if job.started_at:
                job.duration_ms = int(
                    (finished - job.started_at).total_seconds() * 1000
                )
            record_audit_event(
                db,
                action=ACTION_AI_JOB_COMPLETED,
                entity_type=ENTITY_AI_JOB,
                entity_id=job.id,
                actor_user_id=actor.id if actor else job.requested_by,
                metadata={
                    "generation_id": str(generation.id),
                    "tokens_total": result.tokens_total,
                    "estimated_cost_usd": cost,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.commit()
            db.refresh(job)
            return job
        except ProviderNotImplementedError as exc:
            return _fail_job(
                db,
                job,
                str(exc),
                actor=actor,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except (StructuredOutputError, ProviderConfigurationError) as exc:
            return _fail_job(
                db,
                job,
                str(exc),
                actor=actor,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        except AIDomainError as exc:
            last_error = exc
            decision = decide_retry(
                current_retries=job.retries,
                error_message=str(exc),
            )
            if not exc.retryable or not decision.should_retry:
                return _fail_job(
                    db,
                    job,
                    str(exc),
                    actor=actor,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            job.retries = decision.next_retry_count
            db.commit()
            sleep_fn(_backoff_seconds(job.retries))
        except Exception as exc:  # noqa: BLE001 — map unexpected to failed job
            last_error = exc
            return _fail_job(
                db,
                job,
                "Unexpected provider failure.",
                actor=actor,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    # Unreachable, but keeps type checkers happy.
    return _fail_job(
        db,
        job,
        str(last_error) if last_error else "Job failed.",
        actor=actor,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def _fail_job(
    db: Session,
    job: AiJob,
    message: str,
    *,
    actor: User | None,
    ip_address: str | None,
    user_agent: str | None,
) -> AiJob:
    job.status = JOB_STATUS_FAILED
    job.error_message = message
    job.finished_at = _utcnow()
    if job.started_at:
        job.duration_ms = int((job.finished_at - job.started_at).total_seconds() * 1000)
    record_audit_event(
        db,
        action=ACTION_AI_JOB_FAILED,
        entity_type=ENTITY_AI_JOB,
        entity_id=job.id,
        actor_user_id=actor.id if actor else job.requested_by,
        metadata={"error": message[:240]},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(job)
    return job
