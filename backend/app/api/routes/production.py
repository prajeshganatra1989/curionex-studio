"""Production Mode API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.user import User
from app.production.stages import PRODUCTION_STAGES
from app.schemas.production import (
    QUALITY_BAND_SET,
    ProductionActivityResponse,
    ProductionMetricsResponse,
    ProductionOverviewResponse,
    ProductionQueueResponse,
    ProductionSettingsResponse,
    ProductionSettingsUpdate,
)
from app.services import production_service

router = APIRouter(prefix="/production", tags=["production"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, production_service.NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, production_service.ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    raise exc


@router.get("/settings", response_model=ProductionSettingsResponse)
def get_production_settings(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("production.view"))],
) -> ProductionSettingsResponse:
    row = production_service.get_or_create_settings(db)
    return ProductionSettingsResponse.model_validate(row, from_attributes=True)


@router.patch("/settings", response_model=ProductionSettingsResponse)
def patch_production_settings(
    payload: ProductionSettingsUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("production.manage"))],
) -> ProductionSettingsResponse:
    ctx = extract_request_audit_context(request)
    try:
        row = production_service.update_settings(
            db,
            payload,
            actor=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except production_service.ValidationError as exc:
        raise _map_error(exc) from None
    return ProductionSettingsResponse.model_validate(row, from_attributes=True)


@router.get("/overview", response_model=ProductionOverviewResponse)
def get_production_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("production.view"))],
) -> ProductionOverviewResponse:
    data = production_service.build_overview(db, current_user)
    return ProductionOverviewResponse.model_validate(data)


@router.get("/queue", response_model=ProductionQueueResponse)
def get_production_queue(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("production.view"))],
    production_stage: str | None = None,
    project_id: UUID | None = None,
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    search: str | None = None,
    quality_band: str | None = None,
    ai_job_status: str | None = None,
    stale_quality: bool | None = None,
    blocked_only: bool = False,
    pending_approval: bool = False,
    script_status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str | None = Query(default="priority"),
) -> ProductionQueueResponse:
    if production_stage is not None:
        cleaned = production_stage.strip().lower()
        if cleaned not in PRODUCTION_STAGES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid production_stage filter.",
            )
        production_stage = cleaned
    if quality_band is not None:
        cleaned_band = quality_band.strip().lower()
        if cleaned_band not in QUALITY_BAND_SET:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid quality_band filter.",
            )
        quality_band = cleaned_band

    try:
        items, total = production_service.build_queue(
            db,
            current_user,
            production_stage=production_stage,
            project_id=project_id,
            category_id=category_id,
            tag_id=tag_id,
            search=search,
            quality_band=quality_band,
            ai_job_status=ai_job_status,
            stale_quality=stale_quality,
            blocked_only=blocked_only,
            pending_approval=pending_approval,
            script_status=script_status,
            page=page,
            page_size=page_size,
            sort=sort,
        )
    except production_service.ValidationError as exc:
        raise _map_error(exc) from None
    return ProductionQueueResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/metrics", response_model=ProductionMetricsResponse)
def get_production_metrics(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("production.view"))],
    range: str = Query(default="7d", pattern="^(today|7d|30d)$"),
) -> ProductionMetricsResponse:
    try:
        data = production_service.build_metrics(
            db, current_user, range=range  # type: ignore[arg-type]
        )
    except production_service.ValidationError as exc:
        raise _map_error(exc) from None
    return ProductionMetricsResponse.model_validate(data)


@router.get("/activity", response_model=ProductionActivityResponse)
def get_production_activity(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("production.view"))],
    limit: int = Query(20, ge=1, le=100),
) -> ProductionActivityResponse:
    data = production_service.list_recent_activity(db, current_user, limit=limit)
    return ProductionActivityResponse.model_validate(data)
