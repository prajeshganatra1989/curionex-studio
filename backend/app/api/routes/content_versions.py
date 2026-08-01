"""Content version and approval API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.content_version import (
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalReviewRequest,
    ContentVersionCreate,
    ContentVersionListResponse,
    ContentVersionResponse,
)
from app.services import content_version_service

project_versions_router = APIRouter(
    prefix="/projects/{project_id}/content-versions",
    tags=["content-versions"],
)
versions_router = APIRouter(prefix="/content-versions", tags=["content-versions"])
approvals_router = APIRouter(prefix="/approvals", tags=["approvals"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, content_version_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, content_version_service.ForbiddenError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, content_version_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(exc, content_version_service.ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


@project_versions_router.post(
    "",
    response_model=ContentVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_content_version(
    project_id: UUID,
    payload: ContentVersionCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.create"))
    ],
) -> ContentVersionResponse:
    ctx = extract_request_audit_context(request)
    try:
        version = content_version_service.create_content_version(
            db,
            project_id,
            payload,
            creator=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ConflictError,
        content_version_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@project_versions_router.get("", response_model=ContentVersionListResponse)
def get_content_versions(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> ContentVersionListResponse:
    try:
        items, total = content_version_service.list_content_versions(
            db,
            project_id,
            user=current_user,
            page=page,
            page_size=page_size,
            status=status_filter,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionListResponse(
        items=[
            ContentVersionResponse.model_validate(item, from_attributes=True)
            for item in items
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@project_versions_router.get("/latest", response_model=ContentVersionResponse)
def get_latest_content_version(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
) -> ContentVersionResponse:
    try:
        version = content_version_service.get_latest_version(
            db,
            project_id,
            user=current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@project_versions_router.get("/approved", response_model=ContentVersionResponse)
def get_approved_content_version(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
) -> ContentVersionResponse:
    try:
        version = content_version_service.get_latest_approved_version(
            db,
            project_id,
            user=current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@versions_router.get("/{version_id}", response_model=ContentVersionResponse)
def get_content_version(
    version_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
) -> ContentVersionResponse:
    try:
        version = content_version_service.get_content_version_for_user(
            db,
            version_id,
            current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@versions_router.post(
    "/{version_id}/new-version",
    response_model=ContentVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_new_version_from_existing(
    version_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.create"))
    ],
) -> ContentVersionResponse:
    ctx = extract_request_audit_context(request)
    try:
        version = content_version_service.create_version_from_existing(
            db,
            version_id,
            creator=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@versions_router.post(
    "/{version_id}/approval-requests",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_approval_request(
    version_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.create"))],
    payload: ApprovalRequestCreate | None = None,
) -> ApprovalResponse:
    ctx = extract_request_audit_context(request)
    body = payload or ApprovalRequestCreate()
    try:
        approval = content_version_service.request_approval(
            db,
            version_id,
            body,
            requester=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@versions_router.get(
    "/{version_id}/approvals",
    response_model=list[ApprovalResponse],
)
def get_version_approvals(
    version_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.view"))],
) -> list[ApprovalResponse]:
    try:
        items = content_version_service.list_approvals_for_version(
            db,
            version_id,
            user=current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return [
        ApprovalResponse.model_validate(item, from_attributes=True) for item in items
    ]


@approvals_router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.view"))],
) -> ApprovalResponse:
    try:
        approval = content_version_service.get_approval_for_user(
            db,
            approval_id,
            current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@approvals_router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def post_approve(
    approval_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.review"))],
    payload: ApprovalReviewRequest | None = None,
) -> ApprovalResponse:
    ctx = extract_request_audit_context(request)
    body = payload or ApprovalReviewRequest()
    try:
        approval = content_version_service.approve_approval(
            db,
            approval_id,
            body,
            reviewer=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@approvals_router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def post_reject(
    approval_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.review"))],
    payload: ApprovalReviewRequest | None = None,
) -> ApprovalResponse:
    ctx = extract_request_audit_context(request)
    body = payload or ApprovalReviewRequest()
    try:
        approval = content_version_service.reject_approval(
            db,
            approval_id,
            body,
            reviewer=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalResponse.model_validate(approval, from_attributes=True)


@approvals_router.post("/{approval_id}/cancel", response_model=ApprovalResponse)
def post_cancel(
    approval_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.create"))],
    payload: ApprovalReviewRequest | None = None,
) -> ApprovalResponse:
    ctx = extract_request_audit_context(request)
    body = payload or ApprovalReviewRequest()
    try:
        approval = content_version_service.cancel_approval(
            db,
            approval_id,
            body,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalResponse.model_validate(approval, from_attributes=True)
