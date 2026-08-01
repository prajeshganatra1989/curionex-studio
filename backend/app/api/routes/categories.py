"""Category taxonomy API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import project_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def get_categories(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("projects.view"))],
    active_only: bool = Query(default=False),
) -> list[CategoryResponse]:
    items = project_service.list_categories(db, active_only=active_only)
    return [CategoryResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def post_category(
    payload: CategoryCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.create"))],
) -> CategoryResponse:
    ctx = extract_request_audit_context(request)
    try:
        category = project_service.create_category(
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
    return CategoryResponse.model_validate(category, from_attributes=True)


@router.patch("/{category_id}", response_model=CategoryResponse)
def patch_category(
    category_id: UUID,
    payload: CategoryUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.update"))],
) -> CategoryResponse:
    ctx = extract_request_audit_context(request)
    try:
        category = project_service.update_category(
            db,
            category_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        ) from None
    except project_service.ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return CategoryResponse.model_validate(category, from_attributes=True)
