"""Script workspace API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.script import Script
from app.models.user import User
from app.schemas.script import (
    ScriptCreate,
    ScriptDocumentResponse,
    ScriptDocumentUpdate,
    ScriptListItem,
    ScriptListResponse,
    ScriptResponse,
    ScriptUpdate,
)
from app.services import script_service

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
    if isinstance(exc, script_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, script_service.ForbiddenError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, script_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
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
