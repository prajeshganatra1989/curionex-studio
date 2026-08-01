"""Knowledge Pack domain services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.audit.actions import (
    ACTION_KNOWLEDGE_PACK_ARCHIVED,
    ACTION_KNOWLEDGE_PACK_CREATED,
    ACTION_KNOWLEDGE_PACK_SECTION_UPDATED,
    ACTION_KNOWLEDGE_PACK_SECTIONS_REORDERED,
    ACTION_KNOWLEDGE_PACK_UPDATED,
    ENTITY_KNOWLEDGE_PACK,
)
from app.knowledge_packs.catalog import initial_section_definitions
from app.knowledge_packs.constants import (
    KNOWLEDGE_PACK_STATUS_ARCHIVED,
    KNOWLEDGE_PACK_STATUSES,
)
from app.models.knowledge_pack import KnowledgePack, KnowledgePackSection
from app.models.project import Project
from app.models.user import User
from app.schemas.knowledge_pack import (
    KnowledgePackCreate,
    KnowledgePackSectionUpdate,
    KnowledgePackUpdate,
)
from app.services import project_service
from app.services.audit_service import record_audit_event


class NotFoundError(Exception):
    """Raised when a Knowledge Pack or section cannot be found."""


class ForbiddenError(Exception):
    """Raised when the user lacks project membership access."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


class ConflictError(Exception):
    """Raised for uniqueness conflicts."""


def assert_project_access(db: Session, project_id: UUID, user: User) -> Project:
    """Require project existence and membership.

    Global ``knowledge_packs.*`` permissions still gate the route. Membership
    ensures the caller belongs to the project and cannot mutate unrelated packs
    with only a platform-wide grant.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")
    if not project_service.is_project_member(db, project_id, user.id):
        raise ForbiddenError("You do not have access to this project.")
    return project


def _pack_query():
    return select(KnowledgePack).options(
        selectinload(KnowledgePack.sections),
    )


def get_knowledge_pack(db: Session, knowledge_pack_id: UUID) -> KnowledgePack:
    pack = db.scalar(_pack_query().where(KnowledgePack.id == knowledge_pack_id))
    if pack is None:
        raise NotFoundError("Knowledge Pack not found.")
    # Ensure sections are ordered deterministically.
    pack.sections.sort(key=lambda section: (section.position, section.section_key))
    return pack


def get_knowledge_pack_for_user(
    db: Session,
    knowledge_pack_id: UUID,
    user: User,
) -> KnowledgePack:
    pack = get_knowledge_pack(db, knowledge_pack_id)
    assert_project_access(db, pack.project_id, user)
    return pack


def create_knowledge_pack(
    db: Session,
    project_id: UUID,
    payload: KnowledgePackCreate,
    *,
    creator: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> KnowledgePack:
    """Create a pack and initial empty section shells in one transaction."""
    assert_project_access(db, project_id, creator)
    if payload.status not in KNOWLEDGE_PACK_STATUSES:
        raise ValidationError("Invalid knowledge pack status.")

    pack = KnowledgePack(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        created_by=creator.id,
    )
    db.add(pack)
    try:
        db.flush()
        for definition in initial_section_definitions():
            db.add(
                KnowledgePackSection(
                    knowledge_pack_id=pack.id,
                    section_key=definition.key,
                    title=definition.title,
                    content="",
                    position=definition.position,
                )
            )
        record_audit_event(
            db,
            actor_user_id=creator.id,
            action=ACTION_KNOWLEDGE_PACK_CREATED,
            entity_type=ENTITY_KNOWLEDGE_PACK,
            entity_id=pack.id,
            metadata={
                "project_id": str(project_id),
                "status": pack.status,
                "section_count": len(initial_section_definitions()),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to create Knowledge Pack due to a conflict.") from exc

    return get_knowledge_pack(db, pack.id)


def list_knowledge_packs(
    db: Session,
    project_id: UUID,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[KnowledgePack], int]:
    assert_project_access(db, project_id, user)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = [KnowledgePack.project_id == project_id]
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in KNOWLEDGE_PACK_STATUSES:
            raise ValidationError("Invalid status filter.")
        filters.append(KnowledgePack.status == cleaned)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(KnowledgePack.name.ilike(pattern))

    count_stmt = select(func.count()).select_from(KnowledgePack)
    list_stmt = (
        select(KnowledgePack)
        .order_by(KnowledgePack.created_at.desc(), KnowledgePack.id.asc())
    )
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return items, total


def update_knowledge_pack(
    db: Session,
    knowledge_pack_id: UUID,
    payload: KnowledgePackUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> KnowledgePack:
    pack = get_knowledge_pack_for_user(db, knowledge_pack_id, actor)
    changed: list[str] = []

    if payload.name is not None and payload.name != pack.name:
        pack.name = payload.name
        changed.append("name")
    if payload.description is not None and payload.description != pack.description:
        pack.description = payload.description
        changed.append("description")
    if payload.status is not None and payload.status != pack.status:
        pack.status = payload.status
        changed.append("status")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_KNOWLEDGE_PACK_UPDATED,
            entity_type=ENTITY_KNOWLEDGE_PACK,
            entity_id=pack.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()

    return get_knowledge_pack(db, pack.id)


def archive_knowledge_pack(
    db: Session,
    knowledge_pack_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> KnowledgePack:
    """Archive a Knowledge Pack. Does not physically delete pack or sections."""
    pack = get_knowledge_pack_for_user(db, knowledge_pack_id, actor)
    if pack.status == KNOWLEDGE_PACK_STATUS_ARCHIVED:
        return pack

    pack.status = KNOWLEDGE_PACK_STATUS_ARCHIVED
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_KNOWLEDGE_PACK_ARCHIVED,
        entity_type=ENTITY_KNOWLEDGE_PACK,
        entity_id=pack.id,
        metadata={"project_id": str(pack.project_id), "changed_fields": ["status"]},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_knowledge_pack(db, pack.id)


def list_sections(
    db: Session,
    knowledge_pack_id: UUID,
    *,
    actor: User,
) -> list[KnowledgePackSection]:
    pack = get_knowledge_pack_for_user(db, knowledge_pack_id, actor)
    return list(pack.sections)


def get_section(
    db: Session,
    knowledge_pack_id: UUID,
    section_key: str,
    *,
    actor: User,
) -> KnowledgePackSection:
    pack = get_knowledge_pack_for_user(db, knowledge_pack_id, actor)
    for section in pack.sections:
        if section.section_key == section_key:
            return section
    raise NotFoundError("Section not found.")


def update_section(
    db: Session,
    knowledge_pack_id: UUID,
    section_key: str,
    payload: KnowledgePackSectionUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> KnowledgePackSection:
    section = get_section(db, knowledge_pack_id, section_key, actor=actor)
    changed: list[str] = []

    if payload.title is not None and payload.title != section.title:
        section.title = payload.title
        changed.append("title")
    if payload.content is not None and payload.content != section.content:
        section.content = payload.content
        changed.append("content")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_KNOWLEDGE_PACK_SECTION_UPDATED,
            entity_type=ENTITY_KNOWLEDGE_PACK,
            entity_id=knowledge_pack_id,
            metadata={"section_key": section_key, "changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        db.refresh(section)
    return section


def reorder_sections(
    db: Session,
    knowledge_pack_id: UUID,
    section_keys: list[str],
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> list[KnowledgePackSection]:
    """Atomically reorder sections. Rejects partial/unknown/duplicate keys."""
    pack = get_knowledge_pack_for_user(db, knowledge_pack_id, actor)
    requested = [key.strip() for key in section_keys]
    if not requested or any(not key for key in requested):
        raise ValidationError("Reorder list must contain non-empty section keys.")

    current_keys = [section.section_key for section in pack.sections]
    current_set = set(current_keys)

    if len(requested) != len(set(requested)):
        raise ValidationError("Reorder list must not contain duplicate section keys.")
    if set(requested) != current_set:
        missing = sorted(current_set - set(requested))
        unknown = sorted(set(requested) - current_set)
        details: list[str] = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown keys: {', '.join(unknown)}")
        raise ValidationError(
            "Reorder list must include each current section key exactly once"
            + (f" ({'; '.join(details)})" if details else ".")
        )
    if len(requested) != len(current_keys):
        raise ValidationError("Reorder list length must match current section count.")

    by_key = {section.section_key: section for section in pack.sections}
    # Two-phase update avoids transient unique collisions if a unique
    # (pack, position) index is added later; keeps reorder atomic in one commit.
    for offset, key in enumerate(requested, start=1):
        by_key[key].position = offset + 10_000
    db.flush()
    for offset, key in enumerate(requested, start=1):
        by_key[key].position = offset

    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_KNOWLEDGE_PACK_SECTIONS_REORDERED,
        entity_type=ENTITY_KNOWLEDGE_PACK,
        entity_id=knowledge_pack_id,
        metadata={"section_order": requested},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return list(get_knowledge_pack(db, knowledge_pack_id).sections)
