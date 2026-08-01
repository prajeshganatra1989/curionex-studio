"""Project management API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.context import extract_request_audit_context
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    CategoryResponse,
    MessageResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
    TagResponse,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_to_response(project: Project) -> ProjectResponse:
    tags = [
        TagResponse.model_validate(link.tag, from_attributes=True)
        for link in project.project_tags
        if link.tag is not None
    ]
    category = (
        CategoryResponse.model_validate(project.category, from_attributes=True)
        if project.category is not None
        else None
    )
    return ProjectResponse(
        id=project.id,
        project_code=project.project_code,
        name=project.name,
        description=project.description,
        status=project.status,
        category_id=project.category_id,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        category=category,
        tags=tags,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def post_project(
    payload: ProjectCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.create"))],
) -> ProjectResponse:
    ctx = extract_request_audit_context(request)
    try:
        project = project_service.create_project(
            db,
            payload,
            creator=current_user,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
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
    return _project_to_response(project)


@router.get("", response_model=ProjectListResponse)
def get_projects(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("projects.view"))],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    created_by: UUID | None = None,
    search: str | None = None,
) -> ProjectListResponse:
    try:
        items, total = project_service.list_projects(
            db,
            page=page,
            page_size=page_size,
            status=status_filter,
            category_id=category_id,
            tag_id=tag_id,
            created_by=created_by,
            search=search,
        )
    except project_service.ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    return ProjectListResponse(
        items=[_project_to_response(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("projects.view"))],
) -> ProjectResponse:
    try:
        project = project_service.get_project(db, project_id)
    except project_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from None
    return _project_to_response(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
def patch_project(
    project_id: UUID,
    payload: ProjectUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.update"))],
) -> ProjectResponse:
    ctx = extract_request_audit_context(request)
    try:
        project = project_service.update_project(
            db,
            project_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except project_service.ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return _project_to_response(project)


@router.delete("/{project_id}", response_model=ProjectResponse)
def delete_project(
    project_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.delete"))],
) -> ProjectResponse:
    """Archive a project. Rows are retained for future content references."""
    ctx = extract_request_audit_context(request)
    try:
        project = project_service.archive_project(
            db,
            project_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from None
    return _project_to_response(project)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
def get_project_members(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_permission("projects.view"))],
) -> list[ProjectMemberResponse]:
    try:
        members = project_service.list_project_members(db, project_id)
    except project_service.NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        ) from None
    return [
        ProjectMemberResponse(
            user_id=member.user_id,
            email=member.user.email,
            first_name=member.user.first_name,
            last_name=member.user.last_name,
            created_at=member.created_at,
        )
        for member in members
    ]


@router.post(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_project_member(
    project_id: UUID,
    user_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.update"))],
) -> ProjectMemberResponse:
    ctx = extract_request_audit_context(request)
    try:
        member = project_service.add_project_member(
            db,
            project_id,
            user_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    except project_service.ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None
    return ProjectMemberResponse(
        user_id=member.user_id,
        email=member.user.email,
        first_name=member.user.first_name,
        last_name=member.user.last_name,
        created_at=member.created_at,
    )


@router.delete(
    "/{project_id}/members/{user_id}",
    response_model=MessageResponse,
)
def delete_project_member(
    project_id: UUID,
    user_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission("projects.update"))],
) -> MessageResponse:
    ctx = extract_request_audit_context(request)
    try:
        project_service.remove_project_member(
            db,
            project_id,
            user_id,
            actor_user_id=current_user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
    except project_service.NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from None
    return MessageResponse(detail="Project member removed.")
