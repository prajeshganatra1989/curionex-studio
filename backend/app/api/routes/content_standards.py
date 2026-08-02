"""Content Standard API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.content_standard import (
    ContentStandardCreate,
    ContentStandardListResponse,
    ContentStandardResponse,
    ContentStandardSummaryResponse,
    ContentStandardUpdate,
)
from app.services import content_standard_service

router = APIRouter(prefix="/content-standards", tags=["content-standards"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, content_standard_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, content_standard_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, content_standard_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    raise exc


@router.get("/active", response_model=ContentStandardResponse)
def get_active_content_standard(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("content_standards.view"))],
) -> ContentStandardResponse:
    standard = content_standard_service.get_active(db)
    if standard is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active content standard.",
        )
    return ContentStandardResponse.model_validate(standard)


@router.get("/summary", response_model=ContentStandardSummaryResponse)
def get_content_standard_summary(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("content_standards.view"))],
) -> ContentStandardSummaryResponse:
    standard = content_standard_service.get_active(db)
    if standard is None:
        return ContentStandardSummaryResponse(has_active=False)
    return ContentStandardSummaryResponse(
        id=standard.id,
        name=standard.name,
        version=standard.version,
        status=standard.status,
        label=f"{standard.name} v{standard.version}",
        updated_at=standard.updated_at,
        has_active=True,
    )


@router.get("", response_model=ContentStandardListResponse)
def list_content_standards(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("content_standards.view"))],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    include_archived: Annotated[bool, Query()] = True,
) -> ContentStandardListResponse:
    try:
        items = content_standard_service.list_standards(
            db,
            status=status_filter,
            include_archived=include_archived,
        )
    except content_standard_service.ValidationError as exc:
        raise _map_error(exc) from None
    return ContentStandardListResponse(
        items=[ContentStandardResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.get("/{standard_id}", response_model=ContentStandardResponse)
def get_content_standard(
    standard_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("content_standards.view"))],
) -> ContentStandardResponse:
    try:
        standard = content_standard_service.get_standard(db, standard_id)
    except content_standard_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return ContentStandardResponse.model_validate(standard)


@router.post(
    "",
    response_model=ContentStandardResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_content_standard(
    payload: ContentStandardCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_permission("content_standards.manage"))],
) -> ContentStandardResponse:
    ctx = extract_request_audit_context(request)
    try:
        standard = content_standard_service.create_standard(
            db,
            payload,
            actor=actor,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_standard_service.ConflictError,
        content_standard_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentStandardResponse.model_validate(standard)


@router.patch("/{standard_id}", response_model=ContentStandardResponse)
def update_content_standard(
    standard_id: UUID,
    payload: ContentStandardUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_permission("content_standards.manage"))],
) -> ContentStandardResponse:
    ctx = extract_request_audit_context(request)
    try:
        standard = content_standard_service.update_standard(
            db,
            standard_id,
            payload,
            actor=actor,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_standard_service.NotFoundError,
        content_standard_service.ConflictError,
        content_standard_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentStandardResponse.model_validate(standard)


@router.post("/{standard_id}/activate", response_model=ContentStandardResponse)
def activate_content_standard(
    standard_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_permission("content_standards.manage"))],
) -> ContentStandardResponse:
    ctx = extract_request_audit_context(request)
    try:
        standard = content_standard_service.activate_standard(
            db,
            standard_id,
            actor=actor,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except content_standard_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return ContentStandardResponse.model_validate(standard)


@router.post("/{standard_id}/archive", response_model=ContentStandardResponse)
def archive_content_standard(
    standard_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(require_permission("content_standards.manage"))],
) -> ContentStandardResponse:
    ctx = extract_request_audit_context(request)
    try:
        standard = content_standard_service.archive_standard(
            db,
            standard_id,
            actor=actor,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except content_standard_service.NotFoundError as exc:
        raise _map_error(exc) from None
    return ContentStandardResponse.model_validate(standard)
