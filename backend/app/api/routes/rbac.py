"""RBAC management routes (minimal verification API)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.rbac import (
    MessageResponse,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)
from app.services import rbac_service

router = APIRouter(tags=["rbac"])


@router.get("/roles", response_model=list[RoleResponse])
def get_roles(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("roles.view"))],
) -> list:
    return rbac_service.list_roles(db)


@router.get("/permissions", response_model=list[PermissionResponse])
def get_permissions(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("roles.view"))],
) -> list:
    return rbac_service.list_permissions(db)


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def post_role(
    payload: RoleCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("roles.create"))],
) -> RoleResponse:
    ctx = extract_request_audit_context(request)
    try:
        return rbac_service.create_role(
            db,
            name=payload.name,
            description=payload.description,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except rbac_service.DuplicateRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None


@router.post(
    "/roles/{role_id}/permissions/{permission_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_role_permission(
    role_id: UUID,
    permission_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("roles.update"))],
) -> MessageResponse:
    ctx = extract_request_audit_context(request)
    try:
        rbac_service.assign_permission_to_role(
            db,
            role_id=role_id,
            permission_id=permission_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except rbac_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role or permission not found.",
        ) from None
    except rbac_service.DuplicateAssignmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return MessageResponse(detail="Permission assigned to role.")


@router.post(
    "/users/{user_id}/roles/{role_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_user_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("roles.assign"))],
) -> MessageResponse:
    ctx = extract_request_audit_context(request)
    try:
        rbac_service.assign_role_to_user(
            db,
            user_id=user_id,
            role_id=role_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except rbac_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User or role not found.",
        ) from None
    except rbac_service.DuplicateAssignmentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return MessageResponse(detail="Role assigned to user.")


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    response_model=MessageResponse,
)
def delete_user_role(
    user_id: UUID,
    role_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("roles.assign"))],
) -> MessageResponse:
    ctx = extract_request_audit_context(request)
    try:
        rbac_service.remove_role_from_user(
            db,
            user_id=user_id,
            role_id=role_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except rbac_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User role assignment not found.",
        ) from None
    return MessageResponse(detail="Role removed from user.")
