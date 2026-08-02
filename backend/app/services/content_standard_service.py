"""Content Standard domain service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_CONTENT_STANDARD_ACTIVATED,
    ACTION_CONTENT_STANDARD_ARCHIVED,
    ACTION_CONTENT_STANDARD_CREATED,
    ACTION_CONTENT_STANDARD_UPDATED,
    ENTITY_CONTENT_STANDARD,
)
from app.editorial.content_standard_constants import (
    CONTENT_STANDARD_STATUS_ACTIVE,
    CONTENT_STANDARD_STATUS_ARCHIVED,
    CONTENT_STANDARD_STATUSES,
)
from app.editorial.content_standard_prompt import get_active_content_standard
from app.editorial.content_standard_seed import CONTENT_STANDARD_V1
from app.models.content_standard import ContentStandard
from app.models.user import User
from app.schemas.content_standard import ContentStandardCreate, ContentStandardUpdate
from app.services.audit_service import record_audit_event


class NotFoundError(Exception):
    """Raised when a content standard does not exist."""


class ConflictError(Exception):
    """Raised for uniqueness / single-active conflicts."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


_TEXT_FIELDS = (
    "mission",
    "target_audience",
    "brand_voice",
    "editorial_principles",
    "hook_rules",
    "story_structure",
    "fact_policy",
    "citation_policy",
    "tone_guidelines",
    "language_rules",
    "forbidden_patterns",
    "approved_cta_patterns",
    "quality_checklist",
)


def list_standards(
    db: Session,
    *,
    status: str | None = None,
    include_archived: bool = True,
) -> list[ContentStandard]:
    stmt = select(ContentStandard).order_by(
        ContentStandard.created_at.desc(),
        ContentStandard.version.desc(),
    )
    if status is not None:
        if status not in CONTENT_STANDARD_STATUSES:
            raise ValidationError(
                f"status must be one of: {', '.join(sorted(CONTENT_STANDARD_STATUSES))}"
            )
        stmt = stmt.where(ContentStandard.status == status)
    elif not include_archived:
        stmt = stmt.where(ContentStandard.status != CONTENT_STANDARD_STATUS_ARCHIVED)
    return list(db.scalars(stmt).all())


def get_standard(db: Session, standard_id: UUID) -> ContentStandard:
    standard = db.get(ContentStandard, standard_id)
    if standard is None:
        raise NotFoundError("Content standard not found.")
    return standard


def get_active(db: Session) -> ContentStandard | None:
    return get_active_content_standard(db)


def _archive_active(
    db: Session,
    *,
    actor: User | None,
    except_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> list[ContentStandard]:
    archived: list[ContentStandard] = []
    stmt = select(ContentStandard).where(
        ContentStandard.status == CONTENT_STANDARD_STATUS_ACTIVE
    )
    if except_id is not None:
        stmt = stmt.where(ContentStandard.id != except_id)
    for row in db.scalars(stmt).all():
        row.status = CONTENT_STANDARD_STATUS_ARCHIVED
        archived.append(row)
        record_audit_event(
            db,
            action=ACTION_CONTENT_STANDARD_ARCHIVED,
            entity_type=ENTITY_CONTENT_STANDARD,
            entity_id=row.id,
            actor_user_id=actor.id if actor else None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"version": row.version, "reason": "superseded_by_activation"},
        )
    return archived


def create_standard(
    db: Session,
    payload: ContentStandardCreate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentStandard:
    status = payload.status
    if status not in CONTENT_STANDARD_STATUSES:
        raise ValidationError(
            f"status must be one of: {', '.join(sorted(CONTENT_STANDARD_STATUSES))}"
        )
    if status == CONTENT_STANDARD_STATUS_ACTIVE:
        _archive_active(
            db,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    existing = db.scalars(
        select(ContentStandard).where(ContentStandard.version == payload.version)
    ).first()
    if existing is not None:
        raise ConflictError(f"Version '{payload.version}' already exists.")

    standard = ContentStandard(
        name=payload.name.strip(),
        version=payload.version.strip(),
        status=status,
        mission=payload.mission.strip(),
        target_audience=payload.target_audience.strip(),
        brand_voice=payload.brand_voice.strip(),
        editorial_principles=payload.editorial_principles.strip(),
        hook_rules=payload.hook_rules.strip(),
        story_structure=payload.story_structure.strip(),
        fact_policy=payload.fact_policy.strip(),
        citation_policy=payload.citation_policy.strip(),
        tone_guidelines=payload.tone_guidelines.strip(),
        language_rules=payload.language_rules.strip(),
        forbidden_patterns=payload.forbidden_patterns.strip(),
        approved_cta_patterns=payload.approved_cta_patterns.strip(),
        quality_checklist=payload.quality_checklist.strip(),
        default_duration_seconds=payload.default_duration_seconds,
        default_target_words=payload.default_target_words,
        notes=payload.notes.strip() if payload.notes else None,
        created_by=actor.id,
    )
    db.add(standard)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to create content standard.") from exc

    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_CREATED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"version": standard.version, "status": standard.status},
    )
    if status == CONTENT_STANDARD_STATUS_ACTIVE:
        record_audit_event(
            db,
            action=ACTION_CONTENT_STANDARD_ACTIVATED,
            entity_type=ENTITY_CONTENT_STANDARD,
            entity_id=standard.id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"version": standard.version},
        )
    db.commit()
    db.refresh(standard)
    return standard


def update_standard(
    db: Session,
    standard_id: UUID,
    payload: ContentStandardUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentStandard:
    standard = get_standard(db, standard_id)
    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        raise ValidationError("Use the activate or archive endpoints to change status.")
    if "version" in data:
        new_version = str(data["version"]).strip()
        if new_version != standard.version:
            clash = db.scalars(
                select(ContentStandard).where(
                    ContentStandard.version == new_version,
                    ContentStandard.id != standard.id,
                )
            ).first()
            if clash is not None:
                raise ConflictError(f"Version '{new_version}' already exists.")
            standard.version = new_version

    if "name" in data and data["name"] is not None:
        standard.name = str(data["name"]).strip()
    for field in _TEXT_FIELDS:
        if field in data and data[field] is not None:
            setattr(standard, field, str(data[field]).strip())
    if (
        "default_duration_seconds" in data
        and data["default_duration_seconds"] is not None
    ):
        standard.default_duration_seconds = int(data["default_duration_seconds"])
    if "default_target_words" in data and data["default_target_words"] is not None:
        standard.default_target_words = int(data["default_target_words"])
    if "notes" in data:
        notes = data["notes"]
        standard.notes = (
            notes.strip() if isinstance(notes, str) and notes.strip() else None
        )

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to update content standard.") from exc

    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_UPDATED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"version": standard.version, "fields": sorted(data.keys())},
    )
    db.commit()
    db.refresh(standard)
    return standard


def activate_standard(
    db: Session,
    standard_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentStandard:
    standard = get_standard(db, standard_id)
    if standard.status == CONTENT_STANDARD_STATUS_ACTIVE:
        return standard

    _archive_active(
        db,
        actor=actor,
        except_id=standard.id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    standard.status = CONTENT_STANDARD_STATUS_ACTIVE
    db.flush()
    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_ACTIVATED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"version": standard.version},
    )
    db.commit()
    db.refresh(standard)
    return standard


def archive_standard(
    db: Session,
    standard_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentStandard:
    standard = get_standard(db, standard_id)
    if standard.status == CONTENT_STANDARD_STATUS_ARCHIVED:
        return standard

    standard.status = CONTENT_STANDARD_STATUS_ARCHIVED
    db.flush()
    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_ARCHIVED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata={"version": standard.version},
    )
    db.commit()
    db.refresh(standard)
    return standard


def ensure_content_standard_v1(
    db: Session,
    *,
    actor: User | None = None,
) -> ContentStandard:
    """Idempotently seed Content Standard v1 as the active standard."""
    existing = db.scalars(
        select(ContentStandard).where(
            ContentStandard.version == CONTENT_STANDARD_V1["version"]
        )
    ).first()
    if existing is not None:
        if existing.status != CONTENT_STANDARD_STATUS_ACTIVE:
            # Prefer keeping whatever is already active; only activate if none.
            active = get_active(db)
            if active is None:
                existing.status = CONTENT_STANDARD_STATUS_ACTIVE
                db.commit()
                db.refresh(existing)
        return existing

    _archive_active(db, actor=actor)
    standard = ContentStandard(
        **{key: value for key, value in CONTENT_STANDARD_V1.items() if key != "status"},
        status=CONTENT_STANDARD_STATUS_ACTIVE,
        created_by=actor.id if actor else None,
    )
    db.add(standard)
    db.flush()
    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_CREATED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id if actor else None,
        metadata={"version": standard.version, "seeded": True},
    )
    record_audit_event(
        db,
        action=ACTION_CONTENT_STANDARD_ACTIVATED,
        entity_type=ENTITY_CONTENT_STANDARD,
        entity_id=standard.id,
        actor_user_id=actor.id if actor else None,
        metadata={"version": standard.version, "seeded": True},
    )
    db.commit()
    db.refresh(standard)
    return standard
