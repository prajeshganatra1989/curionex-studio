"""Content production workflow API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.content_version import Approval, ContentVersion
from app.models.script import Script
from app.models.user import User
from app.models.workflow import ContentWorkflow
from app.schemas.workflow import (
    ContentWorkflowResponse,
    WorkflowApprovalSummary,
    WorkflowReviewResponse,
    WorkflowScriptSummary,
    WorkflowStatusResponse,
    WorkflowTransitionRequest,
    WorkflowVersionCreateResponse,
    WorkflowVersionRef,
    WorkflowVersionSummary,
)
from app.services import content_version_service, workflow_service

workflows_router = APIRouter(prefix="/scripts/{script_id}/workflow", tags=["workflows"])


def _version_summary(version: ContentVersion) -> WorkflowVersionSummary:
    return WorkflowVersionSummary(
        id=version.id,
        version_number=version.version_number,
        status=version.status,
        title=version.title,
        created_at=version.created_at,
    )


def _version_ref(version: ContentVersion | None) -> WorkflowVersionRef | None:
    if version is None:
        return None
    return WorkflowVersionRef(
        id=version.id,
        version_number=version.version_number,
        status=version.status,
        title=version.title,
    )


def _approval_summary(approval: Approval) -> WorkflowApprovalSummary:
    return WorkflowApprovalSummary(
        id=approval.id,
        status=approval.status,
        content_version_id=approval.content_version_id,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
    )


def _workflow_response(
    workflow: ContentWorkflow,
    script: Script | None = None,
    latest_approval: Approval | None = None,
) -> ContentWorkflowResponse:
    active = workflow.active_content_version
    script_summary = None
    knowledge_pack_id = None
    if script is not None:
        knowledge_pack_id = script.knowledge_pack_id
        script_summary = WorkflowScriptSummary(
            id=script.id,
            script_code=script.script_code,
            title=script.title,
            status=script.status,
            knowledge_pack_id=script.knowledge_pack_id,
            project_id=script.project_id,
        )
    return ContentWorkflowResponse(
        id=workflow.id,
        script_id=workflow.script_id,
        current_stage=workflow.current_stage,
        status=workflow.status,
        active_content_version_id=workflow.active_content_version_id,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        script=script_summary,
        knowledge_pack_id=knowledge_pack_id,
        active_content_version=_version_summary(active) if active else None,
        latest_approval=_approval_summary(latest_approval) if latest_approval else None,
    )


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(
        exc,
        (
            workflow_service.NotFoundError,
            content_version_service.NotFoundError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        (
            workflow_service.ForbiddenError,
            content_version_service.ForbiddenError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(
        exc,
        (
            workflow_service.ValidationError,
            content_version_service.ValidationError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    if isinstance(
        exc,
        (
            workflow_service.ConflictError,
            content_version_service.ConflictError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    raise exc


@workflows_router.get("", response_model=ContentWorkflowResponse)
def get_workflow(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("workflows.view"))],
) -> ContentWorkflowResponse:
    try:
        workflow, script, latest_approval = workflow_service.get_workflow_detail(
            db, script_id, user=current_user
        )
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return _workflow_response(workflow, script, latest_approval)


@workflows_router.get("/status", response_model=WorkflowStatusResponse)
def get_workflow_status(
    script_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("workflows.view"))],
) -> WorkflowStatusResponse:
    try:
        payload = workflow_service.get_workflow_status(
            db, script_id, user=current_user
        )
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    pending = payload["pending_approval"]
    return WorkflowStatusResponse(
        script_id=payload["script_id"],
        stage=payload["stage"],
        status=payload["status"],
        active_version=_version_ref(payload["active_version"]),
        latest_version=_version_ref(payload["latest_version"]),
        approved_version=_version_ref(payload["approved_version"]),
        pending_approval=_approval_summary(pending) if pending else None,
    )


@workflows_router.post("/transition", response_model=ContentWorkflowResponse)
def post_transition(
    script_id: UUID,
    payload: WorkflowTransitionRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("workflows.update"))],
) -> ContentWorkflowResponse:
    ctx = extract_request_audit_context(request)
    try:
        workflow = workflow_service.transition_workflow(
            db,
            script_id,
            payload.target_stage,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        script = workflow_service.get_workflow_for_user(db, script_id, current_user)[1]
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
        workflow_service.ValidationError,
        workflow_service.ConflictError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return _workflow_response(workflow, script)


@workflows_router.post(
    "/create-version",
    response_model=WorkflowVersionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_create_version(
    script_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("scripts.update"))],
) -> WorkflowVersionCreateResponse:
    ctx = extract_request_audit_context(request)
    try:
        workflow, version = workflow_service.create_version_from_workspace(
            db,
            script_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        script = workflow_service.get_workflow_for_user(db, script_id, current_user)[1]
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
        workflow_service.ValidationError,
        workflow_service.ConflictError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return WorkflowVersionCreateResponse(
        workflow=_workflow_response(workflow, script),
        content_version=_version_summary(version),
    )


@workflows_router.post(
    "/submit-review",
    response_model=WorkflowReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_submit_review(
    script_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("workflows.update"))],
) -> WorkflowReviewResponse:
    ctx = extract_request_audit_context(request)
    try:
        workflow, approval, version = workflow_service.submit_review(
            db,
            script_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        script = workflow_service.get_workflow_for_user(db, script_id, current_user)[1]
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
        workflow_service.ValidationError,
        workflow_service.ConflictError,
        content_version_service.ValidationError,
        content_version_service.ConflictError,
        content_version_service.NotFoundError,
        content_version_service.ForbiddenError,
    ) as exc:
        raise _map_error(exc) from None
    return WorkflowReviewResponse(
        workflow=_workflow_response(workflow, script, approval),
        approval=_approval_summary(approval),
        content_version=_version_summary(version),
    )


@workflows_router.post("/archive", response_model=ContentWorkflowResponse)
def post_archive(
    script_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("workflows.update"))],
) -> ContentWorkflowResponse:
    ctx = extract_request_audit_context(request)
    try:
        workflow = workflow_service.archive_workflow(
            db,
            script_id,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        script = workflow_service.get_workflow_for_user(db, script_id, current_user)[1]
    except (
        workflow_service.NotFoundError,
        workflow_service.ForbiddenError,
        workflow_service.ValidationError,
        workflow_service.ConflictError,
    ) as exc:
        raise _map_error(exc) from None
    return _workflow_response(workflow, script)
