"""Script workspace API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.api.routes import ai as ai_routes
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.script import Script
from app.models.user import User
from app.production.package_schemas import (
    ProductionPackageEligibilityResponse,
    ProductionPackageResponse,
)
from app.schemas.ai import (
    AiGenerationListResponse,
    AiGenerationResponse,
    AiJobResponse,
    ScriptAiDraftApply,
    ScriptAiDraftApplyResponse,
    ScriptAiDraftCreate,
    ScriptAiPrerequisitesResponse,
    ScriptQualityReviewCreate,
    ScriptQualitySuggestionApply,
    ScriptQualitySuggestionApplyResponse,
)
from app.schemas.script import (
    ScriptCreate,
    ScriptDocumentResponse,
    ScriptDocumentUpdate,
    ScriptListItem,
    ScriptListResponse,
    ScriptResponse,
    ScriptUpdate,
)
from app.services import (
    production_package_service,
    script_ai_service,
    script_quality_service,
    script_service,
)

project_scripts_router = APIRouter(
    prefix="/projects/{project_id}/scripts",
    tags=["scripts"],
)
scripts_router = APIRouter(prefix="/scripts", tags=["scripts"])


def _script_to_response(script: Script) -> ScriptResponse:
    documents = sorted(script.documents, key=lambda d: (d.position, d.document_type))
    return ScriptResponse(
        id=script.id,
        project_id=script.project_id,
        knowledge_pack_id=script.knowledge_pack_id,
        script_code=script.script_code,
        title=script.title,
        description=script.description,
        status=script.status,
        content_version_id=script.content_version_id,
        created_by=script.created_by,
        created_at=script.created_at,
        updated_at=script.updated_at,
        documents=[
            ScriptDocumentResponse.model_validate(doc, from_attributes=True)
            for doc in documents
        ],
    )


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            script_service.NotFoundError,
            script_ai_service.NotFoundError,
            script_quality_service.NotFoundError,
            production_package_service.NotFoundError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        (
            script_service.ForbiddenError,
            script_ai_service.ForbiddenError,
            script_quality_service.ForbiddenError,
            production_package_service.ForbiddenError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, production_package_service.NotGoldApprovedError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.reason, "message": str(exc)},
        )
    if isinstance(exc, script_ai_service.PrerequisiteError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": exc.code,
                "missing": list(exc.missing),
                "message": str(exc),
            },
        )
    if isinstance(exc, script_quality_service.StaleReviewError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "message": str(exc)},
        )
    if isinstance(exc, script_quality_service.ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": exc.code, "message": str(exc)},
        )
    if isinstance(
        exc,
        (
            script_service.ValidationError,
            script_ai_service.ValidationError,
            script_quality_service.ValidationError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, script_ai_service.ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "conflicts": list(exc.conflicts)},
        )
    if isinstance(exc, script_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


@project_scripts_router.post(
    "",
    response_model=ScriptResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_script(
    project_id: UUID,
    payload: ScriptCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.create"))],
) -> ScriptResponse:
    ctx = extract_request_audit_context(request)
    try:
        script = script_service.create_script(
            db,
            project_id,
            payload,
            creator=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
        script_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return _script_to_response(script)


@project_scripts_router.get("", response_model=ScriptListResponse)
def get_project_scripts(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
) -> ScriptListResponse:
    try:
        items, total = script_service.list_scripts(
            db,
            project_id,
            user=current_user,
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
    except (
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptListResponse(
        items=[
            ScriptListItem.model_validate(item, from_attributes=True) for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@scripts_router.get("/{script_id}", response_model=ScriptResponse)
def get_script(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> ScriptResponse:
    try:
        script = script_service.get_script_for_user(db, script_id, current_user)
    except (script_service.NotFoundError, script_service.ForbiddenError) as exc:
        raise _map_error(exc) from None
    return _script_to_response(script)


@scripts_router.patch("/{script_id}", response_model=ScriptResponse)
def patch_script(
    script_id: UUID,
    payload: ScriptUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.update"))],
) -> ScriptResponse:
    ctx = extract_request_audit_context(request)
    try:
        script = script_service.update_script(
            db,
            script_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
        script_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return _script_to_response(script)


@scripts_router.delete("/{script_id}", response_model=ScriptResponse)
def delete_script(
    script_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.delete"))],
) -> ScriptResponse:
    """Archive a script. Documents remain for historical reference."""
    ctx = extract_request_audit_context(request)
    try:
        script = script_service.archive_script(
            db,
            script_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (script_service.NotFoundError, script_service.ForbiddenError) as exc:
        raise _map_error(exc) from None
    return _script_to_response(script)


@scripts_router.get(
    "/{script_id}/documents",
    response_model=list[ScriptDocumentResponse],
)
def get_documents(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> list[ScriptDocumentResponse]:
    try:
        documents = script_service.list_documents(
            db, script_id, actor=current_user
        )
    except (script_service.NotFoundError, script_service.ForbiddenError) as exc:
        raise _map_error(exc) from None
    return [
        ScriptDocumentResponse.model_validate(doc, from_attributes=True)
        for doc in documents
    ]


@scripts_router.get(
    "/{script_id}/documents/{document_type}",
    response_model=ScriptDocumentResponse,
)
def get_document(
    script_id: UUID,
    document_type: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> ScriptDocumentResponse:
    try:
        document = script_service.get_document(
            db, script_id, document_type, actor=current_user
        )
    except (
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptDocumentResponse.model_validate(document, from_attributes=True)


@scripts_router.patch(
    "/{script_id}/documents/{document_type}",
    response_model=ScriptDocumentResponse,
)
def patch_document(
    script_id: UUID,
    document_type: str,
    payload: ScriptDocumentUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.update"))],
) -> ScriptDocumentResponse:
    ctx = extract_request_audit_context(request)
    try:
        document = script_service.update_document(
            db,
            script_id,
            document_type,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptDocumentResponse.model_validate(document, from_attributes=True)


@scripts_router.post(
    "/{script_id}/documents/{document_type}/ai-drafts",
    response_model=AiJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_script_document_ai_draft(
    script_id: UUID,
    document_type: str,
    payload: ScriptAiDraftCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.generate"))],
) -> AiJobResponse:
    ctx = extract_request_audit_context(request)
    try:
        job = script_ai_service.create_script_document_draft_job(
            db,
            script_id=script_id,
            document_type=document_type,
            actor=current_user,
            model_id=payload.model_id,
            language=payload.language,
            tone=payload.tone,
            target_duration_seconds=payload.target_duration_seconds,
            target_words_per_minute=payload.target_words_per_minute,
            idempotency_key=payload.idempotency_key,
            execute_now=True,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            sleep_fn=lambda _s: None,
        )
    except (
        script_ai_service.NotFoundError,
        script_ai_service.ForbiddenError,
        script_ai_service.ValidationError,
        script_ai_service.PrerequisiteError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ai_routes._job_response(job, db)


@scripts_router.get(
    "/{script_id}/ai-drafts",
    response_model=AiGenerationListResponse,
)
def get_script_ai_drafts(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.view"))],
    document_type: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AiGenerationListResponse:
    try:
        script_service.get_script_for_user(db, script_id, current_user)
        items, total = script_ai_service.list_script_drafts(
            db,
            script_id,
            document_type=document_type,
            page=page,
            page_size=page_size,
        )
    except (
        script_ai_service.NotFoundError,
        script_ai_service.ForbiddenError,
        script_ai_service.ValidationError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return AiGenerationListResponse(
        items=[ai_routes._generation_response(item, db) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@scripts_router.get(
    "/{script_id}/documents/{document_type}/ai-drafts",
    response_model=AiGenerationListResponse,
)
def get_script_document_ai_drafts(
    script_id: UUID,
    document_type: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AiGenerationListResponse:
    try:
        script_service.get_script_for_user(db, script_id, current_user)
        items, total = script_ai_service.list_script_drafts(
            db,
            script_id,
            document_type=document_type,
            page=page,
            page_size=page_size,
        )
    except (
        script_ai_service.NotFoundError,
        script_ai_service.ForbiddenError,
        script_ai_service.ValidationError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return AiGenerationListResponse(
        items=[ai_routes._generation_response(item, db) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@scripts_router.get(
    "/{script_id}/documents/{document_type}/ai-prerequisites",
    response_model=ScriptAiPrerequisitesResponse,
)
def get_script_document_ai_prerequisites(
    script_id: UUID,
    document_type: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> ScriptAiPrerequisitesResponse:
    try:
        script = script_service.get_script_for_user(db, script_id, current_user)
        cleaned = (document_type or "").strip()
        prerequisites = script_ai_service.get_document_prerequisites(script)
        if cleaned not in prerequisites:
            raise script_ai_service.ValidationError(
                f"Invalid document type: {document_type!r}"
            )
        info = prerequisites[cleaned]
    except (
        script_ai_service.NotFoundError,
        script_ai_service.ForbiddenError,
        script_ai_service.ValidationError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptAiPrerequisitesResponse(
        document_type=cleaned,
        ready=bool(info["ready"]),
        missing=list(info["missing"]),
    )


@scripts_router.post(
    "/{script_id}/documents/{document_type}/ai-generations/{generation_id}/apply",
    response_model=ScriptAiDraftApplyResponse,
)
def post_apply_script_ai_generation(
    script_id: UUID,
    document_type: str,
    generation_id: UUID,
    payload: ScriptAiDraftApply,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.update"))],
) -> ScriptAiDraftApplyResponse:
    ctx = extract_request_audit_context(request)
    try:
        document, generation, stale = (
            script_ai_service.apply_generation_to_script_document(
                db,
                script_id=script_id,
                document_type=document_type,
                generation_id=generation_id,
                conflict_strategy=payload.conflict_strategy,  # type: ignore[arg-type]
                actor=current_user,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            )
        )
    except (
        script_ai_service.NotFoundError,
        script_ai_service.ForbiddenError,
        script_ai_service.ValidationError,
        script_ai_service.ConflictError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptAiDraftApplyResponse(
        document=ScriptDocumentResponse.model_validate(
            document, from_attributes=True
        ).model_dump(mode="json"),
        generation_id=generation.id,
        conflict_strategy=payload.conflict_strategy,
        stale_input=stale,
    )


@scripts_router.post(
    "/{script_id}/ai-quality-reviews",
    response_model=AiJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_script_quality_review(
    script_id: UUID,
    payload: ScriptQualityReviewCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.generate"))],
) -> AiJobResponse:
    ctx = extract_request_audit_context(request)
    try:
        job = script_quality_service.create_quality_review_job(
            db,
            script_id=script_id,
            actor=current_user,
            model_id=payload.model_id,
            language=payload.language,
            target_duration_seconds=payload.target_duration_seconds,
            target_words_per_minute=payload.target_words_per_minute,
            idempotency_key=payload.idempotency_key,
            execute_now=True,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            sleep_fn=lambda _s: None,
        )
    except (
        script_quality_service.NotFoundError,
        script_quality_service.ForbiddenError,
        script_quality_service.ValidationError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ai_routes._job_response(job, db)


@scripts_router.get(
    "/{script_id}/ai-quality-reviews",
    response_model=AiGenerationListResponse,
)
def get_script_quality_reviews(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> AiGenerationListResponse:
    try:
        items, total = script_quality_service.list_quality_reviews(
            db,
            script_id,
            actor=current_user,
            page=page,
            page_size=page_size,
        )
    except (
        script_quality_service.NotFoundError,
        script_quality_service.ForbiddenError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return AiGenerationListResponse(
        items=[ai_routes._generation_response(item, db) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@scripts_router.get(
    "/{script_id}/ai-quality-reviews/latest",
    response_model=AiGenerationResponse,
)
def get_latest_script_quality_review(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.view"))],
) -> AiGenerationResponse:
    try:
        item = script_quality_service.get_latest_quality_review(
            db, script_id, actor=current_user
        )
    except (
        script_quality_service.NotFoundError,
        script_quality_service.ForbiddenError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quality review found for this script.",
        )
    return ai_routes._generation_response(item, db)


@scripts_router.post(
    "/{script_id}/ai-quality-reviews/{generation_id}/suggestions/{issue_id}/apply",
    response_model=ScriptQualitySuggestionApplyResponse,
)
def post_apply_quality_suggestion(
    script_id: UUID,
    generation_id: UUID,
    issue_id: str,
    payload: ScriptQualitySuggestionApply,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.update"))],
) -> ScriptQualitySuggestionApplyResponse:
    ctx = extract_request_audit_context(request)
    try:
        document, generation, stale = script_quality_service.apply_suggestion(
            db,
            script_id=script_id,
            generation_id=generation_id,
            issue_id=issue_id,
            strategy=payload.strategy,  # type: ignore[arg-type]
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        script_quality_service.NotFoundError,
        script_quality_service.ForbiddenError,
        script_quality_service.ValidationError,
        script_quality_service.ConflictError,
        script_quality_service.StaleReviewError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
        script_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ScriptQualitySuggestionApplyResponse(
        document=ScriptDocumentResponse.model_validate(
            document, from_attributes=True
        ).model_dump(mode="json"),
        generation_id=generation.id,
        issue_id=issue_id,
        strategy=payload.strategy,
        stale_input=stale,
    )


@scripts_router.get(
    "/{script_id}/production-package/eligibility",
    response_model=ProductionPackageEligibilityResponse,
)
def get_production_package_eligibility(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> ProductionPackageEligibilityResponse:
    try:
        script = script_service.get_script_for_user(db, script_id, current_user)
        return production_package_service.evaluate_gold_eligibility(
            db, script, actor=current_user
        )
    except (
        production_package_service.NotFoundError,
        production_package_service.ForbiddenError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None


@scripts_router.post(
    "/{script_id}/production-package",
    response_model=ProductionPackageResponse,
)
def post_production_package(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.view"))],
) -> ProductionPackageResponse:
    """Generate a planning-only production package for a Gold-eligible script."""
    try:
        return production_package_service.generate_production_package(
            db, script_id, actor=current_user
        )
    except (
        production_package_service.NotFoundError,
        production_package_service.ForbiddenError,
        production_package_service.NotGoldApprovedError,
        script_service.NotFoundError,
        script_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
