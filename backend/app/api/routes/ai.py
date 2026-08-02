"""AI foundation API routes — providers, prompts, jobs, generations, settings."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.ai import AiJob, AiPrompt, AiPromptVersion, AiProvider
from app.models.user import User
from app.schemas.ai import (
    AiGenerationListResponse,
    AiGenerationResponse,
    AiJobCreate,
    AiJobListResponse,
    AiJobResponse,
    AiModelResponse,
    AiModelUpdate,
    AiPromptCreate,
    AiPromptListResponse,
    AiPromptResponse,
    AiPromptUpdate,
    AiPromptVersionCreate,
    AiPromptVersionResponse,
    AiProviderCredentials,
    AiProviderResponse,
    AiProviderUpdate,
    AiSettingsResponse,
    AiSettingsUpdate,
)
from app.services import ai_service
from app.services.ai_service import provider_has_credentials

router = APIRouter(prefix="/ai", tags=["ai"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ai_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ai_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, ai_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    from app.ai.credentials import CredentialEncryptionError
    from app.services import script_quality_service, script_service

    if isinstance(
        exc,
        (script_quality_service.NotFoundError, script_service.NotFoundError),
    ):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        (script_quality_service.ForbiddenError, script_service.ForbiddenError),
    ):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, CredentialEncryptionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    raise exc


def _provider_response(provider: AiProvider) -> AiProviderResponse:
    return AiProviderResponse(
        id=provider.id,
        code=provider.code,
        name=provider.name,
        is_active=provider.is_active,
        base_url=provider.base_url,
        has_credentials=provider_has_credentials(provider),
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


def _version_response(version: AiPromptVersion) -> AiPromptVersionResponse:
    return AiPromptVersionResponse(
        id=version.id,
        prompt_id=version.prompt_id,
        version_number=version.version_number,
        system_prompt=version.system_prompt,
        user_template=version.user_template,
        variables=[str(item) for item in (version.variables_json or [])],
        status=version.status,
        created_by=version.created_by,
        created_at=version.created_at,
    )


def _prompt_response(db: Session, prompt: AiPrompt) -> AiPromptResponse:
    active = ai_service.get_active_version(db, prompt)
    return AiPromptResponse(
        id=prompt.id,
        name=prompt.name,
        description=prompt.description,
        purpose=prompt.purpose,
        status=prompt.status,
        owner_id=prompt.owner_id,
        active_version_id=prompt.active_version_id,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
        active_version=_version_response(active) if active else None,
    )


def _job_response(job: AiJob, db: Session | None = None) -> AiJobResponse:
    generation_id = None
    if db is not None and job.status == "completed":
        from sqlalchemy import select

        from app.models.ai import AiGeneration

        generation_id = db.scalar(
            select(AiGeneration.id)
            .where(AiGeneration.job_id == job.id)
            .order_by(AiGeneration.created_at.desc())
            .limit(1)
        )
    return AiJobResponse(
        id=job.id,
        status=job.status,
        requested_by=job.requested_by,
        prompt_version_id=job.prompt_version_id,
        model_id=job.model_id,
        input_variables=dict(job.input_variables_json or {}),
        purpose=getattr(job, "purpose", None),
        knowledge_pack_id=getattr(job, "knowledge_pack_id", None),
        project_id=getattr(job, "project_id", None),
        script_id=getattr(job, "script_id", None),
        document_type=getattr(job, "document_type", None),
        idempotency_key=getattr(job, "idempotency_key", None),
        cancel_requested=bool(getattr(job, "cancel_requested", False)),
        generation_id=generation_id,
        started_at=job.started_at,
        finished_at=job.finished_at,
        duration_ms=job.duration_ms,
        retries=job.retries,
        error_message=job.error_message,
        created_at=job.created_at,
    )


def _generation_response(item, db: Session | None = None) -> AiGenerationResponse:
    stale_input = None
    if db is not None and getattr(item, "script_id", None):
        purpose = getattr(item, "purpose", None)
        try:
            if purpose == "script.quality_review":
                from app.services import script_quality_service

                stale_input = script_quality_service.is_generation_stale(db, item)
            elif getattr(item, "document_type", None):
                from app.services import script_ai_service

                stale_input = script_ai_service.is_generation_stale(db, item)
        except Exception:  # noqa: BLE001 — listing must not fail on stale check
            stale_input = None
    return AiGenerationResponse(
        id=item.id,
        job_id=item.job_id,
        prompt_version_id=item.prompt_version_id,
        model_id=item.model_id,
        provider_id=item.provider_id,
        input_variables=dict(item.input_variables_json or {}),
        output_text=item.output_text,
        structured_output=getattr(item, "structured_output_json", None),
        purpose=getattr(item, "purpose", None),
        knowledge_pack_id=getattr(item, "knowledge_pack_id", None),
        project_id=getattr(item, "project_id", None),
        script_id=getattr(item, "script_id", None),
        document_type=getattr(item, "document_type", None),
        tokens_input=item.tokens_input,
        tokens_output=item.tokens_output,
        tokens_total=getattr(item, "tokens_total", None),
        cost_usd=item.cost_usd,
        latency_ms=item.latency_ms,
        provider_request_id=getattr(item, "provider_request_id", None),
        model_identifier=getattr(item, "model_identifier", None),
        temperature=item.temperature,
        seed=item.seed,
        applied_sections=[
            str(x) for x in (getattr(item, "applied_sections_json", None) or [])
        ],
        applied_at=getattr(item, "applied_at", None),
        warnings=[str(x) for x in (getattr(item, "warnings_json", None) or [])],
        input_fingerprint=getattr(item, "input_fingerprint_json", None),
        stale_input=stale_input,
        created_at=item.created_at,
    )


@router.get("/providers", response_model=list[AiProviderResponse])
def get_providers(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> list[AiProviderResponse]:
    return [_provider_response(item) for item in ai_service.list_providers(db)]


@router.get("/providers/{provider_id}", response_model=AiProviderResponse)
def get_provider(
    provider_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiProviderResponse:
    try:
        provider = ai_service.get_provider(db, provider_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return _provider_response(provider)


@router.patch("/providers/{provider_id}", response_model=AiProviderResponse)
def patch_provider(
    provider_id: UUID,
    payload: AiProviderUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.manage"))],
) -> AiProviderResponse:
    ctx = extract_request_audit_context(request)
    try:
        provider = ai_service.update_provider(
            db,
            provider_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (ai_service.NotFoundError, ai_service.ValidationError) as exc:
        raise _map_error(exc) from None
    return _provider_response(provider)


@router.post(
    "/providers/{provider_id}/credentials",
    response_model=AiProviderResponse,
)
def post_provider_credentials(
    provider_id: UUID,
    payload: AiProviderCredentials,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.manage"))],
) -> AiProviderResponse:
    from app.ai.credentials import CredentialEncryptionError

    ctx = extract_request_audit_context(request)
    try:
        provider = ai_service.set_provider_credentials(
            db,
            provider_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        ai_service.NotFoundError,
        ai_service.ValidationError,
        CredentialEncryptionError,
    ) as exc:
        raise _map_error(exc) from None
    return _provider_response(provider)


@router.delete(
    "/providers/{provider_id}/credentials",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_provider_credentials(
    provider_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.manage"))],
) -> None:
    ctx = extract_request_audit_context(request)
    try:
        ai_service.clear_provider_credentials(
            db,
            provider_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None


@router.get("/models", response_model=list[AiModelResponse])
def get_models(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
    provider_id: Annotated[UUID | None, Query()] = None,
) -> list[AiModelResponse]:
    models = ai_service.list_models(db, provider_id=provider_id)
    return [
        AiModelResponse.model_validate(item, from_attributes=True) for item in models
    ]


@router.get("/models/{model_id}", response_model=AiModelResponse)
def get_model(
    model_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiModelResponse:
    try:
        model = ai_service.get_model(db, model_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return AiModelResponse.model_validate(model, from_attributes=True)


@router.patch("/models/{model_id}", response_model=AiModelResponse)
def patch_model(
    model_id: UUID,
    payload: AiModelUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.manage"))],
) -> AiModelResponse:
    ctx = extract_request_audit_context(request)
    try:
        model = ai_service.update_model(
            db,
            model_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return AiModelResponse.model_validate(model, from_attributes=True)


@router.get("/prompts", response_model=AiPromptListResponse)
def get_prompts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query()] = None,
) -> AiPromptListResponse:
    items, total = ai_service.list_prompts(
        db, page=page, page_size=page_size, status=status_filter, search=search
    )
    return AiPromptListResponse(
        items=[_prompt_response(db, item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/prompts",
    response_model=AiPromptResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_prompt(
    payload: AiPromptCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("prompt.manage"))],
) -> AiPromptResponse:
    ctx = extract_request_audit_context(request)
    try:
        prompt = ai_service.create_prompt(
            db,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except ai_service.ValidationError as exc:
        raise _map_error(exc) from None
    return _prompt_response(db, prompt)


@router.get("/prompts/{prompt_id}", response_model=AiPromptResponse)
def get_prompt(
    prompt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiPromptResponse:
    try:
        prompt = ai_service.get_prompt(db, prompt_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return _prompt_response(db, prompt)


@router.patch("/prompts/{prompt_id}", response_model=AiPromptResponse)
def patch_prompt(
    prompt_id: UUID,
    payload: AiPromptUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("prompt.manage"))],
) -> AiPromptResponse:
    ctx = extract_request_audit_context(request)
    try:
        prompt = ai_service.update_prompt(
            db,
            prompt_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (ai_service.NotFoundError, ai_service.ValidationError) as exc:
        raise _map_error(exc) from None
    return _prompt_response(db, prompt)


@router.get(
    "/prompts/{prompt_id}/versions",
    response_model=list[AiPromptVersionResponse],
)
def get_prompt_versions(
    prompt_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> list[AiPromptVersionResponse]:
    try:
        versions = ai_service.list_prompt_versions(db, prompt_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return [_version_response(item) for item in versions]


@router.post(
    "/prompts/{prompt_id}/versions",
    response_model=AiPromptVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_prompt_version(
    prompt_id: UUID,
    payload: AiPromptVersionCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("prompt.manage"))],
) -> AiPromptVersionResponse:
    ctx = extract_request_audit_context(request)
    try:
        version = ai_service.create_prompt_version(
            db,
            prompt_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (ai_service.NotFoundError, ai_service.ValidationError) as exc:
        raise _map_error(exc) from None
    return _version_response(version)


@router.post(
    "/prompts/{prompt_id}/versions/{version_id}/activate",
    response_model=AiPromptResponse,
)
def post_activate_prompt_version(
    prompt_id: UUID,
    version_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("prompt.manage"))],
) -> AiPromptResponse:
    ctx = extract_request_audit_context(request)
    try:
        prompt = ai_service.activate_prompt_version(
            db,
            prompt_id,
            version_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return _prompt_response(db, prompt)


@router.get("/jobs", response_model=AiJobListResponse)
def get_jobs(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> AiJobListResponse:
    items, total = ai_service.list_jobs(
        db, page=page, page_size=page_size, status=status_filter
    )
    return AiJobListResponse(
        items=[_job_response(item, db) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/jobs/{job_id}", response_model=AiJobResponse)
def get_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiJobResponse:
    try:
        job = ai_service.get_job(db, job_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return _job_response(job, db)


@router.post(
    "/jobs",
    response_model=AiJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_job(
    payload: AiJobCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.generate"))],
) -> AiJobResponse:
    ctx = extract_request_audit_context(request)
    try:
        job = ai_service.create_job(
            db,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (ai_service.NotFoundError, ai_service.ValidationError) as exc:
        raise _map_error(exc) from None
    return _job_response(job, db)


@router.post("/jobs/{job_id}/cancel", response_model=AiJobResponse)
def post_cancel_job(
    job_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.generate"))],
) -> AiJobResponse:
    ctx = extract_request_audit_context(request)
    try:
        job = ai_service.cancel_job(
            db,
            job_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (ai_service.NotFoundError, ai_service.ConflictError) as exc:
        raise _map_error(exc) from None
    return _job_response(job, db)


@router.get("/generations", response_model=AiGenerationListResponse)
def get_generations(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    project_id: Annotated[UUID | None, Query()] = None,
    script_id: Annotated[UUID | None, Query()] = None,
    document_type: Annotated[str | None, Query()] = None,
    purpose: Annotated[str | None, Query()] = None,
    provider_id: Annotated[UUID | None, Query()] = None,
    model_id: Annotated[UUID | None, Query()] = None,
    knowledge_pack_id: Annotated[UUID | None, Query()] = None,
    applied: Annotated[bool | None, Query()] = None,
) -> AiGenerationListResponse:
    items, total = ai_service.list_generations(
        db,
        page=page,
        page_size=page_size,
        project_id=project_id,
        script_id=script_id,
        document_type=document_type,
        purpose=purpose,
        provider_id=provider_id,
        model_id=model_id,
        knowledge_pack_id=knowledge_pack_id,
        applied=applied,
    )
    return AiGenerationListResponse(
        items=[_generation_response(item, db) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/generations/{generation_id}", response_model=AiGenerationResponse)
def get_generation(
    generation_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiGenerationResponse:
    try:
        item = ai_service.get_generation(db, generation_id)
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return _generation_response(item, db)


@router.get("/quality-reviews/{generation_id}", response_model=AiGenerationResponse)
def get_quality_review(
    generation_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiGenerationResponse:
    from app.services import script_quality_service

    try:
        item = script_quality_service.get_quality_review(
            db, generation_id, actor=current_user
        )
    except (
        script_quality_service.NotFoundError,
        script_quality_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return _generation_response(item, db)


@router.get("/settings", response_model=AiSettingsResponse)
def get_settings(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiSettingsResponse:
    row = ai_service.get_or_create_settings(db)
    return AiSettingsResponse.model_validate(row, from_attributes=True)


@router.put("/settings", response_model=AiSettingsResponse)
def put_settings(
    payload: AiSettingsUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.manage"))],
) -> AiSettingsResponse:
    ctx = extract_request_audit_context(request)
    try:
        row = ai_service.update_settings(
            db,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except ai_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return AiSettingsResponse.model_validate(row, from_attributes=True)
