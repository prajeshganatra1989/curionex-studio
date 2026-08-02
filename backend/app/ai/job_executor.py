"""Synchronous AI job execution with retries (OpenAI live path)."""

from __future__ import annotations

import json
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
from app.ai.script_draft import (
    MASTER_SCRIPT_MAX_REPAIR_ATTEMPTS,
    PURPOSE_MASTER_SCRIPT,
    SCRIPT_DRAFT_PURPOSES,
    parse_master_script,
    schema_and_parser_for_purpose,
    target_word_range,
    word_count,
)
from app.audit.actions import (
    ACTION_AI_JOB_COMPLETED,
    ACTION_AI_JOB_FAILED,
    ACTION_AI_JOB_STARTED,
    ACTION_SCRIPT_AI_DRAFT_COMPLETED,
    ACTION_SCRIPT_AI_DRAFT_FAILED,
    ENTITY_AI_JOB,
    ENTITY_SCRIPT,
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


def _maybe_repair_master_script_duration(
    *,
    adapter,
    request: GenerationRequest,
    structured: dict,
    variables: dict,
    model: AiModel,
    max_repairs: int,
) -> tuple[dict, list[str], int, int, float]:
    """One bounded repair attempt when narration word count is out of tolerance.

    Completes with a warning if still mismatched — does not fail the job.
    """
    warnings: list[str] = []
    repair_in = 0
    repair_out = 0
    repair_cost = 0.0

    try:
        duration = int(str(variables.get("target_duration_seconds", 60)))
    except (TypeError, ValueError):
        duration = 60
    try:
        wpm = int(str(variables.get("target_words_per_minute", 150)))
    except (TypeError, ValueError):
        wpm = 150

    lo, target, hi = target_word_range(
        target_duration_seconds=max(1, duration),
        target_words_per_minute=max(1, wpm),
    )
    draft = parse_master_script(structured)
    count = word_count(draft.narration)
    if lo <= count <= hi:
        return structured, warnings, repair_in, repair_out, repair_cost

    if max_repairs < 1:
        warnings.append(
            f"Narration word count {count} outside target range "
            f"{lo}-{hi} (target {target}); no repair attempted."
        )
        return structured, warnings, repair_in, repair_out, repair_cost

    repair_request = GenerationRequest(
        model_code=request.model_code,
        system_prompt=(
            request.system_prompt
            + "\n\nDURATION CORRECTION ONLY: Rewrite the narration to approximately "
            f"{target} words (acceptable {lo}-{hi}) while preserving meaning, hook, "
            "and payoff. Return the same JSON schema."
        ),
        user_prompt=(
            "Correct only the narration length for this Master Script draft JSON:\n"
            + json.dumps(structured)
        ),
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        response_json_schema=request.response_json_schema,
        response_schema_name=request.response_schema_name,
        supports_structured_output=request.supports_structured_output,
        supports_temperature=request.supports_temperature,
        api_key=request.api_key,
        base_url=request.base_url,
    )
    try:
        repaired = adapter.generate(repair_request)
    except Exception:  # noqa: BLE001
        warnings.append(
            f"Narration word count {count} outside target range {lo}-{hi}; "
            "duration repair call failed."
        )
        return structured, warnings, repair_in, repair_out, repair_cost

    repair_in = repaired.tokens_input or 0
    repair_out = repaired.tokens_output or 0
    extra = estimate_cost_usd(
        tokens_input=repaired.tokens_input,
        tokens_output=repaired.tokens_output,
        pricing_input_per_1k=model.pricing_input_per_1k,
        pricing_output_per_1k=model.pricing_output_per_1k,
    )
    if extra:
        repair_cost = extra

    if repaired.structured_output:
        try:
            draft = parse_master_script(repaired.structured_output)
            structured = draft.model_dump()
            count = word_count(draft.narration)
        except Exception:  # noqa: BLE001
            warnings.append("Duration repair returned invalid structured output.")
            return structured, warnings, repair_in, repair_out, repair_cost

    if lo <= count <= hi:
        warnings.append(
            f"Duration repaired to {count} words (target range {lo}-{hi})."
        )
    else:
        warnings.append(
            f"Narration word count {count} still outside target range "
            f"{lo}-{hi} after one repair attempt."
        )
    return structured, warnings, repair_in, repair_out, repair_cost


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
    elif job.purpose in SCRIPT_DRAFT_PURPOSES:
        schema, _parser, schema_name = schema_and_parser_for_purpose(job.purpose)

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
            warnings: list[str] = []
            repair_tokens_in = 0
            repair_tokens_out = 0
            repair_cost_extra = 0.0
            if schema is not None:
                if structured is None:
                    raise StructuredOutputError(
                        "Provider returned no structured output."
                    )
                # Force verify status + schema validation.
                if job.purpose == PURPOSE_KNOWLEDGE_PACK_DRAFT:
                    draft = parse_knowledge_pack_draft(structured)
                    structured = draft.model_dump()
                else:
                    _, parser, _ = schema_and_parser_for_purpose(job.purpose)
                    draft = parser(structured)
                    structured = draft.model_dump()

                    if job.purpose == PURPOSE_MASTER_SCRIPT:
                        (
                            structured,
                            warnings,
                            repair_tokens_in,
                            repair_tokens_out,
                            repair_cost_extra,
                        ) = _maybe_repair_master_script_duration(
                            adapter=adapter,
                            request=request,
                            structured=structured,
                            variables=variables,
                            model=model,
                            max_repairs=MASTER_SCRIPT_MAX_REPAIR_ATTEMPTS,
                        )

            finished = _utcnow()
            tokens_input = (result.tokens_input or 0) + repair_tokens_in
            tokens_output = (result.tokens_output or 0) + repair_tokens_out
            tokens_total = tokens_input + tokens_output if (
                result.tokens_input is not None or repair_tokens_in
            ) else result.tokens_total
            cost = estimate_cost_usd(
                tokens_input=tokens_input or None,
                tokens_output=tokens_output or None,
                pricing_input_per_1k=model.pricing_input_per_1k,
                pricing_output_per_1k=model.pricing_output_per_1k,
            )
            if cost is not None:
                cost = round(cost + repair_cost_extra, 6)
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
                script_id=job.script_id,
                document_type=job.document_type,
                input_fingerprint_json=job.input_fingerprint_json,
                warnings_json=warnings,
                tokens_input=tokens_input or result.tokens_input,
                tokens_output=tokens_output or result.tokens_output,
                tokens_total=tokens_total,
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
            if job.purpose in SCRIPT_DRAFT_PURPOSES and job.script_id is not None:
                record_audit_event(
                    db,
                    action=ACTION_SCRIPT_AI_DRAFT_COMPLETED,
                    entity_type=ENTITY_SCRIPT,
                    entity_id=job.script_id,
                    actor_user_id=actor.id if actor else job.requested_by,
                    metadata={
                        "job_id": str(job.id),
                        "generation_id": str(generation.id),
                        "document_type": job.document_type,
                        "purpose": job.purpose,
                        "provider": provider_row.code,
                        "model": model.code,
                        "prompt_version_id": str(version.id),
                        "tokens_total": tokens_total,
                        "estimated_cost_usd": cost,
                        "warnings_count": len(warnings),
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
    if job.purpose in SCRIPT_DRAFT_PURPOSES and job.script_id is not None:
        record_audit_event(
            db,
            action=ACTION_SCRIPT_AI_DRAFT_FAILED,
            entity_type=ENTITY_SCRIPT,
            entity_id=job.script_id,
            actor_user_id=actor.id if actor else job.requested_by,
            metadata={
                "job_id": str(job.id),
                "document_type": job.document_type,
                "purpose": job.purpose,
                "error": message[:240],
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
    db.commit()
    db.refresh(job)
    return job
