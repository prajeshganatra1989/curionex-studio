"""Knowledge Pack API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.api.routes import ai as ai_routes
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.knowledge_pack import KnowledgePack
from app.models.user import User
from app.schemas.ai import (
    AiJobResponse,
    KnowledgePackAiDraftApply,
    KnowledgePackAiDraftApplyResponse,
    KnowledgePackAiDraftCreate,
)
from app.schemas.knowledge_pack import (
    KnowledgePackCreate,
    KnowledgePackListItem,
    KnowledgePackListResponse,
    KnowledgePackResponse,
    KnowledgePackSectionResponse,
    KnowledgePackSectionUpdate,
    KnowledgePackUpdate,
)
from app.services import knowledge_pack_ai_service, knowledge_pack_service

project_packs_router = APIRouter(
    prefix="/projects/{project_id}/knowledge-packs",
    tags=["knowledge-packs"],
)
packs_router = APIRouter(prefix="/knowledge-packs", tags=["knowledge-packs"])


def _pack_to_response(pack: KnowledgePack) -> KnowledgePackResponse:
    sections = sorted(pack.sections, key=lambda s: (s.position, s.section_key))
    return KnowledgePackResponse(
        id=pack.id,
        project_id=pack.project_id,
        name=pack.name,
        description=pack.description,
        status=pack.status,
        created_by=pack.created_by,
        created_at=pack.created_at,
        updated_at=pack.updated_at,
        sections=[
            KnowledgePackSectionResponse.model_validate(section, from_attributes=True)
            for section in sections
        ],
    )


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            knowledge_pack_service.NotFoundError,
            knowledge_pack_ai_service.NotFoundError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        (
            knowledge_pack_service.ForbiddenError,
            knowledge_pack_ai_service.ForbiddenError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(
        exc,
        (
            knowledge_pack_service.ValidationError,
            knowledge_pack_ai_service.ValidationError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, knowledge_pack_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, knowledge_pack_ai_service.ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(exc),
                "conflicts": exc.conflicts,
            },
        )
    raise exc


@project_packs_router.post(
    "",
    response_model=KnowledgePackResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_knowledge_pack(
    project_id: UUID,
    payload: KnowledgePackCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.create"))
    ],
) -> KnowledgePackResponse:
    ctx = extract_request_audit_context(request)
    try:
        pack = knowledge_pack_service.create_knowledge_pack(
            db,
            project_id,
            payload,
            creator=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
        knowledge_pack_service.ValidationError,
        knowledge_pack_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return _pack_to_response(pack)


@project_packs_router.get("", response_model=KnowledgePackListResponse)
def get_project_knowledge_packs(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("knowledge_packs.view"))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
) -> KnowledgePackListResponse:
    try:
        items, total = knowledge_pack_service.list_knowledge_packs(
            db,
            project_id,
            user=current_user,
            page=page,
            page_size=page_size,
            status=status_filter,
            search=search,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
        knowledge_pack_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return KnowledgePackListResponse(
        items=[
            KnowledgePackListItem.model_validate(item, from_attributes=True)
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@packs_router.get("/{knowledge_pack_id}", response_model=KnowledgePackResponse)
def get_knowledge_pack(
    knowledge_pack_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("knowledge_packs.view"))],
) -> KnowledgePackResponse:
    try:
        pack = knowledge_pack_service.get_knowledge_pack_for_user(
            db,
            knowledge_pack_id,
            current_user,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return _pack_to_response(pack)


@packs_router.patch("/{knowledge_pack_id}", response_model=KnowledgePackResponse)
def patch_knowledge_pack(
    knowledge_pack_id: UUID,
    payload: KnowledgePackUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.update"))
    ],
) -> KnowledgePackResponse:
    ctx = extract_request_audit_context(request)
    try:
        pack = knowledge_pack_service.update_knowledge_pack(
            db,
            knowledge_pack_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
        knowledge_pack_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return _pack_to_response(pack)


@packs_router.delete("/{knowledge_pack_id}", response_model=KnowledgePackResponse)
def delete_knowledge_pack(
    knowledge_pack_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.delete"))
    ],
) -> KnowledgePackResponse:
    """Archive a Knowledge Pack. Rows are retained for future references."""
    ctx = extract_request_audit_context(request)
    try:
        pack = knowledge_pack_service.archive_knowledge_pack(
            db,
            knowledge_pack_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return _pack_to_response(pack)


@packs_router.get(
    "/{knowledge_pack_id}/sections",
    response_model=list[KnowledgePackSectionResponse],
)
def get_sections(
    knowledge_pack_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("knowledge_packs.view"))],
) -> list[KnowledgePackSectionResponse]:
    try:
        sections = knowledge_pack_service.list_sections(
            db,
            knowledge_pack_id,
            actor=current_user,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return [
        KnowledgePackSectionResponse.model_validate(section, from_attributes=True)
        for section in sections
    ]


@packs_router.patch(
    "/{knowledge_pack_id}/sections/reorder",
    response_model=list[KnowledgePackSectionResponse],
)
def patch_sections_reorder(
    knowledge_pack_id: UUID,
    section_keys: list[str],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.update"))
    ],
) -> list[KnowledgePackSectionResponse]:
    """Body is a JSON array of section keys in the desired order."""
    ctx = extract_request_audit_context(request)
    try:
        sections = knowledge_pack_service.reorder_sections(
            db,
            knowledge_pack_id,
            section_keys,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
        knowledge_pack_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return [
        KnowledgePackSectionResponse.model_validate(section, from_attributes=True)
        for section in sections
    ]


@packs_router.get(
    "/{knowledge_pack_id}/sections/{section_key}",
    response_model=KnowledgePackSectionResponse,
)
def get_section(
    knowledge_pack_id: UUID,
    section_key: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("knowledge_packs.view"))],
) -> KnowledgePackSectionResponse:
    try:
        section = knowledge_pack_service.get_section(
            db,
            knowledge_pack_id,
            section_key,
            actor=current_user,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return KnowledgePackSectionResponse.model_validate(section, from_attributes=True)


@packs_router.patch(
    "/{knowledge_pack_id}/sections/{section_key}",
    response_model=KnowledgePackSectionResponse,
)
def patch_section(
    knowledge_pack_id: UUID,
    section_key: str,
    payload: KnowledgePackSectionUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.update"))
    ],
) -> KnowledgePackSectionResponse:
    ctx = extract_request_audit_context(request)
    try:
        section = knowledge_pack_service.update_section(
            db,
            knowledge_pack_id,
            section_key,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
        knowledge_pack_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return KnowledgePackSectionResponse.model_validate(section, from_attributes=True)


@project_packs_router.post(
    "/{knowledge_pack_id}/ai-drafts",
    response_model=AiJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_knowledge_pack_ai_draft(
    project_id: UUID,
    knowledge_pack_id: UUID,
    payload: KnowledgePackAiDraftCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("ai.generate"))],
) -> AiJobResponse:
    ctx = extract_request_audit_context(request)
    try:
        job = knowledge_pack_ai_service.create_knowledge_pack_draft_job(
            db,
            project_id=project_id,
            knowledge_pack_id=knowledge_pack_id,
            actor=current_user,
            model_id=payload.model_id,
            target_audience=payload.target_audience,
            language=payload.language,
            desired_depth=payload.desired_depth,
            idempotency_key=payload.idempotency_key,
            execute_now=True,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            sleep_fn=lambda _s: None,
        )
    except (
        knowledge_pack_ai_service.NotFoundError,
        knowledge_pack_ai_service.ForbiddenError,
        knowledge_pack_ai_service.ValidationError,
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ai_routes._job_response(job, db)


@packs_router.post(
    "/{knowledge_pack_id}/ai-generations/{generation_id}/apply",
    response_model=KnowledgePackAiDraftApplyResponse,
)
def post_apply_ai_generation(
    knowledge_pack_id: UUID,
    generation_id: UUID,
    payload: KnowledgePackAiDraftApply,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("knowledge_packs.update"))
    ],
) -> KnowledgePackAiDraftApplyResponse:
    ctx = extract_request_audit_context(request)
    try:
        pack, generation, applied = (
            knowledge_pack_ai_service.apply_generation_to_knowledge_pack(
                db,
                knowledge_pack_id=knowledge_pack_id,
                generation_id=generation_id,
                sections=payload.sections,
                conflict_strategy=payload.conflict_strategy,  # type: ignore[arg-type]
                actor=current_user,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            )
        )
    except (
        knowledge_pack_ai_service.NotFoundError,
        knowledge_pack_ai_service.ForbiddenError,
        knowledge_pack_ai_service.ValidationError,
        knowledge_pack_ai_service.ConflictError,
        knowledge_pack_service.NotFoundError,
        knowledge_pack_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return KnowledgePackAiDraftApplyResponse(
        knowledge_pack=_pack_to_response(pack).model_dump(mode="json"),
        generation_id=generation.id,
        applied_sections=applied,
        conflict_strategy=payload.conflict_strategy,
    )
