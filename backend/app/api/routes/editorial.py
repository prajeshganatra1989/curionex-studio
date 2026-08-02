"""Editorial Library API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.editorial import (
    CreateProjectFromTopicRequest,
    CreateProjectFromTopicResponse,
    DuplicateTitleWarning,
    EditorialTopicCreate,
    EditorialTopicCreateResponse,
    EditorialTopicListResponse,
    EditorialTopicResponse,
    EditorialTopicSummaryResponse,
    EditorialTopicUpdate,
)
from app.schemas.project import ProjectResponse
from app.services import editorial_service
from app.services.rbac_service import has_permission

router = APIRouter(prefix="/editorial-topics", tags=["editorial-topics"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, editorial_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, editorial_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, editorial_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    raise exc


@router.get("/summary", response_model=EditorialTopicSummaryResponse)
def get_editorial_topic_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("editorial_topics.view"))],
) -> EditorialTopicSummaryResponse:
    return EditorialTopicSummaryResponse.model_validate(
        editorial_service.topic_summary(db)
    )


@router.get("", response_model=EditorialTopicListResponse)
def list_editorial_topics(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("editorial_topics.view"))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    category: Annotated[str | None, Query()] = None,
    difficulty: Annotated[str | None, Query()] = None,
    priority: Annotated[str | None, Query()] = None,
    production_wave: Annotated[int | None, Query(ge=1, le=4)] = None,
    min_evergreen_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    include_archived: Annotated[bool, Query()] = False,
    sort: Annotated[str, Query()] = "updated_at_desc",
) -> EditorialTopicListResponse:
    try:
        items, total = editorial_service.list_topics(
            db,
            page=page,
            page_size=page_size,
            status=status_filter,
            category=category,
            difficulty=difficulty,
            priority=priority,
            production_wave=production_wave,
            min_evergreen_score=min_evergreen_score,
            search=search,
            include_archived=include_archived,
            sort=sort,
        )
    except editorial_service.ValidationError as exc:
        raise _map_error(exc) from None
    return EditorialTopicListResponse(
        items=[EditorialTopicResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "",
    response_model=EditorialTopicCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_editorial_topic(
    payload: EditorialTopicCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("editorial_topics.create"))
    ],
) -> EditorialTopicCreateResponse:
    ctx = extract_request_audit_context(request)
    try:
        topic, duplicate = editorial_service.create_topic(
            db,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (editorial_service.ConflictError, editorial_service.ValidationError) as exc:
        raise _map_error(exc) from None

    warning = None
    if duplicate is not None:
        warning = DuplicateTitleWarning(
            similar_topic_id=duplicate.id,
            similar_title=duplicate.title,
            similar_slug=duplicate.slug,
        )
    return EditorialTopicCreateResponse(
        topic=EditorialTopicResponse.model_validate(topic),
        duplicate_warning=warning,
    )


@router.get("/{topic_id}", response_model=EditorialTopicResponse)
def get_editorial_topic(
    topic_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("editorial_topics.view"))],
) -> EditorialTopicResponse:
    try:
        topic = editorial_service.get_topic(db, topic_id)
    except editorial_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return EditorialTopicResponse.model_validate(topic)


@router.patch("/{topic_id}", response_model=EditorialTopicResponse)
def patch_editorial_topic(
    topic_id: UUID,
    payload: EditorialTopicUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("editorial_topics.update"))
    ],
) -> EditorialTopicResponse:
    ctx = extract_request_audit_context(request)
    try:
        topic = editorial_service.update_topic(
            db,
            topic_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        editorial_service.NotFoundError,
        editorial_service.ConflictError,
        editorial_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return EditorialTopicResponse.model_validate(topic)


@router.delete("/{topic_id}", response_model=EditorialTopicResponse)
def archive_editorial_topic(
    topic_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("editorial_topics.delete"))
    ],
) -> EditorialTopicResponse:
    ctx = extract_request_audit_context(request)
    try:
        topic = editorial_service.archive_topic(
            db,
            topic_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except editorial_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return EditorialTopicResponse.model_validate(topic)


@router.post(
    "/{topic_id}/create-project",
    response_model=CreateProjectFromTopicResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_from_editorial_topic(
    topic_id: UUID,
    payload: CreateProjectFromTopicRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("editorial_topics.update"))
    ],
) -> CreateProjectFromTopicResponse:
    if not has_permission(db, current_user, "projects.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing required permission.",
        )
    ctx = extract_request_audit_context(request)
    try:
        topic, project = editorial_service.create_project_from_topic(
            db,
            topic_id,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        editorial_service.NotFoundError,
        editorial_service.ConflictError,
        editorial_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    # project_service may raise its own errors
    except Exception as exc:
        from app.services import project_service as ps

        if isinstance(exc, (ps.NotFoundError, ps.ConflictError, ps.ValidationError)):
            if isinstance(exc, ps.NotFoundError):
                raise HTTPException(status_code=404, detail=str(exc)) from None
            if isinstance(exc, ps.ConflictError):
                raise HTTPException(status_code=409, detail=str(exc)) from None
            raise HTTPException(status_code=422, detail=str(exc)) from None
        raise

    return CreateProjectFromTopicResponse(
        topic=EditorialTopicResponse.model_validate(topic),
        project=ProjectResponse.model_validate(project),
    )
