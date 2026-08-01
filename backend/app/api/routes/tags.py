"""Tag taxonomy API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import TagCreate, TagResponse, TagUpdate
from app.services import project_service

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def get_tags(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("projects.view"))],
) -> list[TagResponse]:
    items = project_service.list_tags(db)
    return [TagResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def post_tag(
    payload: TagCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.create"))],
) -> TagResponse:
    ctx = extract_request_audit_context(request)
    try:
        tag = project_service.create_tag(
            db,
            payload,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except project_service.ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return TagResponse.model_validate(tag, from_attributes=True)


@router.patch("/{tag_id}", response_model=TagResponse)
def patch_tag(
    tag_id: UUID,
    payload: TagUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.update"))],
) -> TagResponse:
    ctx = extract_request_audit_context(request)
    try:
        tag = project_service.update_tag(
            db,
            tag_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found.",
        ) from None
    except project_service.ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return TagResponse.model_validate(tag, from_attributes=True)
