"""Project management domain services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.audit.actions import (
    ACTION_CATEGORY_CREATED,
    ACTION_CATEGORY_UPDATED,
    ACTION_PROJECT_ARCHIVED,
    ACTION_PROJECT_CREATED,
    ACTION_PROJECT_MEMBER_ADDED,
    ACTION_PROJECT_MEMBER_REMOVED,
    ACTION_PROJECT_UPDATED,
    ACTION_TAG_CREATED,
    ACTION_TAG_UPDATED,
    ENTITY_CATEGORY,
    ENTITY_PROJECT,
    ENTITY_TAG,
)
from app.core.config import settings
from app.models.project import Category, Project, ProjectMember, ProjectTag, Tag
from app.models.user import User
from app.projects.constants import (
    PROJECT_CODE_SEQUENCE,
    PROJECT_STATUS_ARCHIVED,
    PROJECT_STATUSES,
)
from app.schemas.project import (
    CategoryCreate,
    CategoryUpdate,
    ProjectCreate,
    ProjectUpdate,
    TagCreate,
    TagUpdate,
    normalize_slug,
)
from app.services.audit_service import record_audit_event


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""


class ConflictError(Exception):
    """Raised for uniqueness / duplicate conflicts."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


def _slug_from_name(name: str) -> str:
    slug = normalize_slug(name)
    if not slug:
        raise ValidationError("Unable to derive a valid slug from name.")
    return slug


def allocate_project_code(db: Session) -> str:
    """Allocate the next project code using a PostgreSQL sequence.

    Uses ``nextval`` so concurrent creators never race on ``MAX(project_code)``.
    Format: ``{PREFIX}-{N}`` with zero-padding (default ``CRX-0001``).
    """
    next_value = db.scalar(text(f"SELECT nextval('{PROJECT_CODE_SEQUENCE}')"))
    if next_value is None:
        raise RuntimeError("Failed to allocate project code from sequence.")
    width = settings.PROJECT_CODE_PAD_WIDTH
    return f"{settings.PROJECT_CODE_PREFIX}-{int(next_value):0{width}d}"


def _load_tags(db: Session, tag_ids: list[UUID]) -> list[Tag]:
    if not tag_ids:
        return []
    tags = list(db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all())
    found = {tag.id for tag in tags}
    missing = [str(tag_id) for tag_id in tag_ids if tag_id not in found]
    if missing:
        raise NotFoundError(f"Tag not found: {', '.join(missing)}")
    # Preserve request order
    by_id = {tag.id: tag for tag in tags}
    return [by_id[tag_id] for tag_id in tag_ids]


def _get_category(db: Session, category_id: UUID | None) -> Category | None:
    if category_id is None:
        return None
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found.")
    return category


def _project_query():
    return select(Project).options(
        selectinload(Project.category),
        selectinload(Project.project_tags).selectinload(ProjectTag.tag),
    )


def get_project(db: Session, project_id: UUID) -> Project:
    project = db.scalar(_project_query().where(Project.id == project_id))
    if project is None:
        raise NotFoundError("Project not found.")
    return project


def create_project(
    db: Session,
    payload: ProjectCreate,
    *,
    creator: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Project:
    """Create a project, assign creator as member, and audit — one transaction."""
    if payload.status not in PROJECT_STATUSES:
        raise ValidationError("Invalid project status.")

    category = _get_category(db, payload.category_id)
    tags = _load_tags(db, payload.tag_ids)
    project_code = allocate_project_code(db)

    project = Project(
        project_code=project_code,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        category_id=category.id if category else None,
        created_by=creator.id,
    )
    db.add(project)
    try:
        db.flush()
        db.add(ProjectMember(project_id=project.id, user_id=creator.id))
        for tag in tags:
            db.add(ProjectTag(project_id=project.id, tag_id=tag.id))
        record_audit_event(
            db,
            actor_user_id=creator.id,
            action=ACTION_PROJECT_CREATED,
            entity_type=ENTITY_PROJECT,
            entity_id=project.id,
            metadata={
                "project_code": project.project_code,
                "status": project.status,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to create project due to a conflict.") from exc

    return get_project(db, project.id)


def list_projects(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category_id: UUID | None = None,
    tag_id: UUID | None = None,
    created_by: UUID | None = None,
    search: str | None = None,
) -> tuple[list[Project], int]:
    """Return paginated projects with filters. Avoids N+1 via selectinload."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = []
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in PROJECT_STATUSES:
            raise ValidationError("Invalid status filter.")
        filters.append(Project.status == cleaned)
    if category_id is not None:
        filters.append(Project.category_id == category_id)
    if created_by is not None:
        filters.append(Project.created_by == created_by)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            (Project.name.ilike(pattern)) | (Project.project_code.ilike(pattern))
        )
    if tag_id is not None:
        filters.append(
            Project.id.in_(
                select(ProjectTag.project_id).where(ProjectTag.tag_id == tag_id)
            )
        )

    count_stmt = select(func.count()).select_from(Project)
    list_stmt = _project_query().order_by(Project.created_at.desc())
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).unique()
    )
    return items, total


def update_project(
    db: Session,
    project_id: UUID,
    payload: ProjectUpdate,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Project:
    project = get_project(db, project_id)
    changed: list[str] = []

    if payload.name is not None and payload.name != project.name:
        project.name = payload.name
        changed.append("name")
    if payload.description is not None and payload.description != project.description:
        project.description = payload.description
        changed.append("description")
    if payload.status is not None and payload.status != project.status:
        project.status = payload.status
        changed.append("status")
    if "category_id" in payload.model_fields_set:
        category = _get_category(db, payload.category_id)
        new_category_id = category.id if category else None
        if new_category_id != project.category_id:
            project.category_id = new_category_id
            changed.append("category_id")
    if payload.tag_ids is not None:
        tags = _load_tags(db, payload.tag_ids)
        existing = {link.tag_id for link in project.project_tags}
        desired = {tag.id for tag in tags}
        if existing != desired:
            project.project_tags.clear()
            db.flush()
            for tag in tags:
                db.add(ProjectTag(project_id=project.id, tag_id=tag.id))
            changed.append("tags")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_PROJECT_UPDATED,
            entity_type=ENTITY_PROJECT,
            entity_id=project.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("Unable to update project due to a conflict.") from exc

    return get_project(db, project.id)


def archive_project(
    db: Session,
    project_id: UUID,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Project:
    """Archive a project (soft lifecycle). Does not physically delete rows."""
    project = get_project(db, project_id)
    if project.status == PROJECT_STATUS_ARCHIVED:
        return project

    project.status = PROJECT_STATUS_ARCHIVED
    record_audit_event(
        db,
        actor_user_id=actor_user_id,
        action=ACTION_PROJECT_ARCHIVED,
        entity_type=ENTITY_PROJECT,
        entity_id=project.id,
        metadata={"project_code": project.project_code, "changed_fields": ["status"]},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_project(db, project.id)


def list_project_members(db: Session, project_id: UUID) -> list[ProjectMember]:
    get_project(db, project_id)
    statement = (
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at.asc())
    )
    return list(db.scalars(statement).all())


def add_project_member(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ProjectMember:
    get_project(db, project_id)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")

    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if existing is not None:
        raise ConflictError("User is already a member of this project.")

    member = ProjectMember(project_id=project_id, user_id=user_id)
    db.add(member)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_PROJECT_MEMBER_ADDED,
            entity_type=ENTITY_PROJECT,
            entity_id=project_id,
            metadata={"user_id": str(user_id)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("User is already a member of this project.") from exc

    return db.scalar(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )


def remove_project_member(
    db: Session,
    project_id: UUID,
    user_id: UUID,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    get_project(db, project_id)
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if member is None:
        raise NotFoundError("Project membership not found.")

    db.delete(member)
    record_audit_event(
        db,
        actor_user_id=actor_user_id,
        action=ACTION_PROJECT_MEMBER_REMOVED,
        entity_type=ENTITY_PROJECT,
        entity_id=project_id,
        metadata={"user_id": str(user_id)},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()


def is_project_member(db: Session, project_id: UUID, user_id: UUID) -> bool:
    return (
        db.scalar(
            select(ProjectMember.id).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        is not None
    )


# --- Categories ---


def list_categories(db: Session, *, active_only: bool = False) -> list[Category]:
    statement = select(Category).order_by(Category.name.asc())
    if active_only:
        statement = statement.where(Category.is_active.is_(True))
    return list(db.scalars(statement).all())


def create_category(
    db: Session,
    payload: CategoryCreate,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Category:
    slug = payload.slug or _slug_from_name(payload.name)
    category = Category(
        name=payload.name,
        slug=slug,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(category)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_CATEGORY_CREATED,
            entity_type=ENTITY_CATEGORY,
            entity_id=category.id,
            metadata={"slug": category.slug},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("A category with this slug already exists.") from exc
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category_id: UUID,
    payload: CategoryUpdate,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise NotFoundError("Category not found.")

    changed: list[str] = []
    if payload.name is not None and payload.name != category.name:
        category.name = payload.name
        changed.append("name")
    if payload.slug is not None and payload.slug != category.slug:
        category.slug = payload.slug
        changed.append("slug")
    if payload.description is not None and payload.description != category.description:
        category.description = payload.description
        changed.append("description")
    if payload.is_active is not None and payload.is_active != category.is_active:
        category.is_active = payload.is_active
        changed.append("is_active")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_CATEGORY_UPDATED,
            entity_type=ENTITY_CATEGORY,
            entity_id=category.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("A category with this slug already exists.") from exc
        db.refresh(category)
    return category


# --- Tags ---


def list_tags(db: Session) -> list[Tag]:
    return list(db.scalars(select(Tag).order_by(Tag.name.asc())).all())


def create_tag(
    db: Session,
    payload: TagCreate,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Tag:
    slug = payload.slug or _slug_from_name(payload.name)
    tag = Tag(name=payload.name, slug=slug)
    db.add(tag)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_TAG_CREATED,
            entity_type=ENTITY_TAG,
            entity_id=tag.id,
            metadata={"slug": tag.slug},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("A tag with this slug already exists.") from exc
    db.refresh(tag)
    return tag


def update_tag(
    db: Session,
    tag_id: UUID,
    payload: TagUpdate,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Tag:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise NotFoundError("Tag not found.")

    changed: list[str] = []
    if payload.name is not None and payload.name != tag.name:
        tag.name = payload.name
        changed.append("name")
    if payload.slug is not None and payload.slug != tag.slug:
        tag.slug = payload.slug
        changed.append("slug")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor_user_id,
            action=ACTION_TAG_UPDATED,
            entity_type=ENTITY_TAG,
            entity_id=tag.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("A tag with this slug already exists.") from exc
        db.refresh(tag)
    return tag
