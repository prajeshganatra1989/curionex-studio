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
    ApprovalDetailResponse,
    ApprovalListItem,
    ApprovalListResponse,
    ApprovalRequestCreate,
    ApprovalResponse,
    ApprovalReviewRequest,
    ContentVersionCreate,
    ContentVersionListResponse,
    ContentVersionResponse,
    ContentVersionSummary,
    ProjectBrief,
    ScriptBrief,
    UserBrief,
)
from app.services import content_version_service

project_versions_router = APIRouter(
    prefix="/projects/{project_id}/content-versions",
    tags=["content-versions"],
)
script_versions_router = APIRouter(
    prefix="/scripts/{script_id}/content-versions",
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


def _user_brief(user) -> UserBrief:
    return UserBrief(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )


def _approval_list_item(approval) -> ApprovalListItem:
    version = approval.content_version
    project = version.project
    script = version.script
    return ApprovalListItem(
        id=approval.id,
        status=approval.status,
        comment=approval.comment,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        requested_by=_user_brief(approval.requester),
        reviewed_by=_user_brief(approval.reviewer) if approval.reviewer else None,
        content_version=ContentVersionSummary.model_validate(
            version, from_attributes=True
        ),
        project=ProjectBrief(
            id=project.id,
            project_code=project.project_code,
            name=project.name,
        ),
        script=(
            ScriptBrief(
                id=script.id,
                script_code=script.script_code,
                title=script.title,
                project_id=script.project_id,
                knowledge_pack_id=script.knowledge_pack_id,
            )
            if script
            else None
        ),
    )


def _approval_detail(db, approval, *, viewer) -> ApprovalDetailResponse:
    version = content_version_service.get_content_version(
        db, approval.content_version_id
    )
    _ = version.project
    _ = version.script
    _ = approval.requester
    _ = approval.reviewer
    history = content_version_service.list_approvals_for_version(
        db,
        version.id,
        user=viewer,
    )
    item = _approval_list_item(approval)
    return ApprovalDetailResponse(
        id=item.id,
        status=item.status,
        comment=item.comment,
        created_at=item.created_at,
        reviewed_at=item.reviewed_at,
        requested_by=item.requested_by,
        reviewed_by=item.reviewed_by,
        content_version=ContentVersionResponse.model_validate(
            version, from_attributes=True
        ),
        project=item.project,
        script=item.script,
        version_approvals=[
            ApprovalResponse.model_validate(row, from_attributes=True) for row in history
        ],
    )


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


@script_versions_router.get("", response_model=ContentVersionListResponse)
def get_script_content_versions(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> ContentVersionListResponse:
    try:
        items, total = content_version_service.list_script_content_versions(
            db,
            script_id,
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


@script_versions_router.get("/latest", response_model=ContentVersionResponse)
def get_script_latest_content_version(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
) -> ContentVersionResponse:
    try:
        version = content_version_service.get_script_latest_version(
            db,
            script_id,
            user=current_user,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return ContentVersionResponse.model_validate(version, from_attributes=True)


@script_versions_router.get("/approved", response_model=ContentVersionResponse)
def get_script_approved_content_version(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission("content_versions.view"))
    ],
) -> ContentVersionResponse:
    try:
        version = content_version_service.get_script_approved_version(
            db,
            script_id,
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


@approvals_router.get("", response_model=ApprovalListResponse)
def get_approvals(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.view"))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    project_id: UUID | None = None,
    search: str | None = None,
) -> ApprovalListResponse:
    try:
        items, total = content_version_service.list_approvals(
            db,
            user=current_user,
            page=page,
            page_size=page_size,
            status=status_filter,
            project_id=project_id,
            search=search,
        )
    except (
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
        content_version_service.ValidationError,
    ) as exc:
        raise _map_error(exc) from None
    return ApprovalListResponse(
        items=[_approval_list_item(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@approvals_router.get("/{approval_id}", response_model=ApprovalDetailResponse)
def get_approval(
    approval_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("approvals.view"))],
) -> ApprovalDetailResponse:
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
    return _approval_detail(db, approval, viewer=current_user)


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
