"""Editorial Library domain services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.audit.actions import (
    ACTION_EDITORIAL_TOPIC_ARCHIVED,
    ACTION_EDITORIAL_TOPIC_CREATED,
    ACTION_EDITORIAL_TOPIC_PROJECT_LINKED,
    ACTION_EDITORIAL_TOPIC_UPDATED,
    ENTITY_EDITORIAL_TOPIC,
)
from app.editorial.constants import (
    CREATE_PROJECT_ALLOWED_STATUSES,
    TOPIC_STATUS_ARCHIVED,
    TOPIC_STATUS_IDEA,
    TOPIC_STATUS_IN_PROGRESS,
    TOPIC_STATUS_PLANNED,
    TOPIC_STATUS_PROJECT_CREATED,
    TOPIC_STATUS_PUBLISHED,
    TOPIC_STATUSES,
)
from app.models.editorial import EditorialTopic
from app.models.project import Project
from app.models.user import User
from app.schemas.editorial import (
    CreateProjectFromTopicRequest,
    EditorialTopicCreate,
    EditorialTopicUpdate,
    normalize_title_key,
)
from app.schemas.project import ProjectCreate, normalize_slug
from app.services import project_service
from app.services.audit_service import record_audit_event


class NotFoundError(Exception):
    """Raised when a topic does not exist."""


class ConflictError(Exception):
    """Raised for uniqueness / duplicate conflicts."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


def _slug_from_title(title: str) -> str:
    slug = normalize_slug(title)
    if not slug:
        raise ValidationError("Unable to derive a valid slug from title.")
    return slug[:180]


def _topic_query():
    return select(EditorialTopic).options(
        selectinload(EditorialTopic.linked_project),
    )


def get_topic(db: Session, topic_id: UUID) -> EditorialTopic:
    topic = db.scalars(
        _topic_query().where(EditorialTopic.id == topic_id)
    ).first()
    if topic is None:
        raise NotFoundError("Editorial topic not found.")
    return topic


def find_duplicate_title(
    db: Session,
    title: str,
    *,
    exclude_id: UUID | None = None,
) -> EditorialTopic | None:
    """Return an active topic with the same normalized title, if any."""
    key = normalize_title_key(title)
    if not key:
        return None
    topics = list(
        db.scalars(
            select(EditorialTopic).where(
                EditorialTopic.status != TOPIC_STATUS_ARCHIVED
            )
        ).all()
    )
    for topic in topics:
        if exclude_id is not None and topic.id == exclude_id:
            continue
        if normalize_title_key(topic.title) == key:
            return topic
    return None


def list_topics(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    category: str | None = None,
    difficulty: str | None = None,
    min_evergreen_score: int | None = None,
    search: str | None = None,
    include_archived: bool = False,
    sort: str = "updated_at_desc",
) -> tuple[list[EditorialTopic], int]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = []
    if status:
        if status not in TOPIC_STATUSES:
            raise ValidationError(
                f"status must be one of: {', '.join(sorted(TOPIC_STATUSES))}"
            )
        filters.append(EditorialTopic.status == status)
    elif not include_archived:
        filters.append(EditorialTopic.status != TOPIC_STATUS_ARCHIVED)

    if category:
        filters.append(EditorialTopic.category == category.strip())
    if difficulty:
        filters.append(EditorialTopic.difficulty == difficulty)
    if min_evergreen_score is not None:
        if min_evergreen_score < 0 or min_evergreen_score > 100:
            raise ValidationError("min_evergreen_score must be between 0 and 100")
        filters.append(EditorialTopic.evergreen_score >= min_evergreen_score)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                EditorialTopic.title.ilike(term),
                EditorialTopic.description.ilike(term),
                EditorialTopic.slug.ilike(term),
                EditorialTopic.notes.ilike(term),
            )
        )

    count_stmt = select(func.count()).select_from(EditorialTopic)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int(db.scalar(count_stmt) or 0)

    sort_key = (sort or "updated_at_desc").strip().lower()
    if sort_key == "title_asc":
        order = EditorialTopic.title.asc()
    elif sort_key == "evergreen_desc":
        order = EditorialTopic.evergreen_score.desc()
    elif sort_key == "curiosity_desc":
        order = EditorialTopic.curiosity_score.desc()
    elif sort_key == "created_at_desc":
        order = EditorialTopic.created_at.desc()
    else:
        order = EditorialTopic.updated_at.desc()

    stmt = _topic_query()
    if filters:
        stmt = stmt.where(*filters)
    stmt = (
        stmt.order_by(order, EditorialTopic.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(stmt).all())
    return items, total


def create_topic(
    db: Session,
    payload: EditorialTopicCreate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
    allow_duplicate_title: bool = False,
) -> tuple[EditorialTopic, EditorialTopic | None]:
    slug = payload.slug or _slug_from_title(payload.title)
    duplicate = find_duplicate_title(db, payload.title)
    if duplicate is not None and not allow_duplicate_title:
        # Soft warning only — creation still proceeds unless slug conflicts.
        pass

    topic = EditorialTopic(
        slug=slug,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        status=payload.status,
        difficulty=payload.difficulty,
        evergreen_score=payload.evergreen_score,
        curiosity_score=payload.curiosity_score,
        viral_potential=payload.viral_potential,
        estimated_duration_seconds=payload.estimated_duration_seconds,
        target_audience=payload.target_audience,
        source=payload.source,
        notes=payload.notes,
        is_featured=payload.is_featured,
        published_video_url=payload.published_video_url,
    )
    db.add(topic)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("An editorial topic with this slug already exists.") from exc

    record_audit_event(
        db,
        action=ACTION_EDITORIAL_TOPIC_CREATED,
        entity_type=ENTITY_EDITORIAL_TOPIC,
        entity_id=topic.id,
        actor_user_id=actor.id,
        metadata={"slug": topic.slug, "title": topic.title, "category": topic.category},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_topic(db, topic.id), duplicate


def update_topic(
    db: Session,
    topic_id: UUID,
    payload: EditorialTopicUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> EditorialTopic:
    topic = get_topic(db, topic_id)
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return topic

    if "title" in data and data["title"] is not None:
        topic.title = data["title"]
    if "slug" in data and data["slug"] is not None:
        topic.slug = data["slug"]
    for field in (
        "description",
        "category",
        "status",
        "difficulty",
        "evergreen_score",
        "curiosity_score",
        "viral_potential",
        "estimated_duration_seconds",
        "target_audience",
        "source",
        "notes",
        "is_featured",
        "published_video_url",
    ):
        if field in data:
            setattr(topic, field, data[field])

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("An editorial topic with this slug already exists.") from exc

    record_audit_event(
        db,
        action=ACTION_EDITORIAL_TOPIC_UPDATED,
        entity_type=ENTITY_EDITORIAL_TOPIC,
        entity_id=topic.id,
        actor_user_id=actor.id,
        metadata={"slug": topic.slug, "fields": sorted(data.keys())},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_topic(db, topic.id)


def archive_topic(
    db: Session,
    topic_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> EditorialTopic:
    topic = get_topic(db, topic_id)
    if topic.status == TOPIC_STATUS_ARCHIVED:
        return topic
    topic.status = TOPIC_STATUS_ARCHIVED
    record_audit_event(
        db,
        action=ACTION_EDITORIAL_TOPIC_ARCHIVED,
        entity_type=ENTITY_EDITORIAL_TOPIC,
        entity_id=topic.id,
        actor_user_id=actor.id,
        metadata={"slug": topic.slug},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_topic(db, topic.id)


def create_project_from_topic(
    db: Session,
    topic_id: UUID,
    payload: CreateProjectFromTopicRequest,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[EditorialTopic, Project]:
    topic = get_topic(db, topic_id)
    if topic.linked_project_id is not None:
        raise ConflictError("This topic is already linked to a project.")
    if topic.status not in CREATE_PROJECT_ALLOWED_STATUSES:
        raise ValidationError(
            "Topic status must be idea, planned, or in_progress to create a project."
        )

    project_name = payload.name or topic.title
    project_description = payload.description
    if project_description is None and topic.description:
        project_description = topic.description

    project = project_service.create_project(
        db,
        ProjectCreate(
            name=project_name,
            description=project_description,
            category_id=payload.category_id,
            tag_ids=payload.tag_ids,
        ),
        creator=actor,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    topic.linked_project_id = project.id
    topic.status = TOPIC_STATUS_PROJECT_CREATED
    record_audit_event(
        db,
        action=ACTION_EDITORIAL_TOPIC_PROJECT_LINKED,
        entity_type=ENTITY_EDITORIAL_TOPIC,
        entity_id=topic.id,
        actor_user_id=actor.id,
        metadata={
            "slug": topic.slug,
            "project_id": str(project.id),
            "project_code": project.project_code,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_topic(db, topic.id), project


def topic_summary(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(EditorialTopic.status, func.count())
        .where(EditorialTopic.status != TOPIC_STATUS_ARCHIVED)
        .group_by(EditorialTopic.status)
    ).all()
    counts = {status: int(count) for status, count in rows}
    available = counts.get(TOPIC_STATUS_IDEA, 0) + counts.get(TOPIC_STATUS_PLANNED, 0)
    in_progress = counts.get(TOPIC_STATUS_IN_PROGRESS, 0) + counts.get(
        TOPIC_STATUS_PROJECT_CREATED, 0
    )
    published = counts.get(TOPIC_STATUS_PUBLISHED, 0)
    project_created = counts.get(TOPIC_STATUS_PROJECT_CREATED, 0)
    total_active = sum(counts.values())
    return {
        "available": available,
        "in_progress": in_progress,
        "published": published,
        "project_created": project_created,
        "total_active": total_active,
    }


def ensure_unique_slug(db: Session, base_slug: str) -> str:
    """Return base_slug or base_slug-N if taken (used by seed)."""
    slug = base_slug[:180]
    if db.scalar(select(EditorialTopic.id).where(EditorialTopic.slug == slug)) is None:
        return slug
    for index in range(2, 1000):
        candidate = f"{base_slug[:170]}-{index}"
        if (
            db.scalar(select(EditorialTopic.id).where(EditorialTopic.slug == candidate))
            is None
        ):
            return candidate
    raise ConflictError("Unable to allocate a unique slug.")


__all__ = [
    "ConflictError",
    "NotFoundError",
    "ValidationError",
    "archive_topic",
    "create_project_from_topic",
    "create_topic",
    "ensure_unique_slug",
    "find_duplicate_title",
    "get_topic",
    "list_topics",
    "topic_summary",
    "update_topic",
]
