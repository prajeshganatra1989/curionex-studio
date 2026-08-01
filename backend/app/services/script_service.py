"""Script workspace domain services."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.audit.actions import (
    ACTION_SCRIPT_ARCHIVED,
    ACTION_SCRIPT_CREATED,
    ACTION_SCRIPT_DOCUMENT_UPDATED,
    ACTION_SCRIPT_UPDATED,
    ENTITY_SCRIPT,
)
from app.models.knowledge_pack import KnowledgePack
from app.models.project import Project
from app.models.script import Script, ScriptDocument
from app.models.user import User
from app.schemas.script import ScriptCreate, ScriptDocumentUpdate, ScriptUpdate
from app.scripts.catalog import DOCUMENT_TYPES, initial_document_definitions
from app.scripts.constants import (
    DEFAULT_SCRIPT_STATUS,
    SCRIPT_CODE_PAD_WIDTH,
    SCRIPT_STATUS_ARCHIVED,
    SCRIPT_STATUS_TRANSITIONS,
    SCRIPT_STATUSES,
)
from app.services import project_service
from app.services.audit_service import record_audit_event

# Namespace for pg_advisory_xact_lock(classid, objid) — distinct from content versions.
_SCRIPT_LOCK_NAMESPACE = 2


class NotFoundError(Exception):
    """Raised when a script or document cannot be found."""


class ForbiddenError(Exception):
    """Raised when the user lacks project membership access."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


class ConflictError(Exception):
    """Raised for uniqueness / state conflicts."""


def assert_project_access(db: Session, project_id: UUID, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")
    if not project_service.is_project_member(db, project_id, user.id):
        raise ForbiddenError("You do not have access to this project.")
    return project


def _advisory_obj_key(project_id: UUID) -> int:
    value = int.from_bytes(project_id.bytes[:4], byteorder="big", signed=False)
    # Keep within signed 32-bit range for the two-arg advisory lock form.
    if value >= 2**31:
        value -= 2**32
    return value


def allocate_script_code(db: Session, project: Project) -> str:
    """Allocate the next script code under a transaction advisory lock.

    Format: ``{project_code}-S{NN}`` (e.g. ``CRX-0001-S01``).
    Uses ``pg_advisory_xact_lock(2, project_hash)`` so concurrent creators for
    the same project serialize. Unique ``script_code`` remains the safety net.
    """
    db.execute(
        text("SELECT pg_advisory_xact_lock(:ns, :key)"),
        {"ns": _SCRIPT_LOCK_NAMESPACE, "key": _advisory_obj_key(project.id)},
    )
    prefix = f"{project.project_code}-S"
    existing = list(
        db.scalars(
            select(Script.script_code).where(Script.project_id == project.id)
        ).all()
    )
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    for code in existing:
        match = pattern.match(code)
        if match:
            max_num = max(max_num, int(match.group(1)))
    next_num = max_num + 1
    return f"{prefix}{next_num:0{SCRIPT_CODE_PAD_WIDTH}d}"


def _validate_knowledge_pack(
    db: Session,
    project_id: UUID,
    knowledge_pack_id: UUID | None,
) -> KnowledgePack | None:
    if knowledge_pack_id is None:
        return None
    pack = db.get(KnowledgePack, knowledge_pack_id)
    if pack is None:
        raise NotFoundError("Knowledge Pack not found.")
    if pack.project_id != project_id:
        raise ValidationError(
            "Knowledge Pack must belong to the same project as the Script."
        )
    return pack


def _script_query():
    return select(Script).options(selectinload(Script.documents))


def get_script(db: Session, script_id: UUID) -> Script:
    script = db.scalar(_script_query().where(Script.id == script_id))
    if script is None:
        raise NotFoundError("Script not found.")
    script.documents.sort(key=lambda doc: (doc.position, doc.document_type))
    return script


def get_script_for_user(db: Session, script_id: UUID, user: User) -> Script:
    script = get_script(db, script_id)
    assert_project_access(db, script.project_id, user)
    return script


def create_script(
    db: Session,
    project_id: UUID,
    payload: ScriptCreate,
    *,
    creator: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Script:
    project = assert_project_access(db, project_id, creator)
    pack = _validate_knowledge_pack(db, project_id, payload.knowledge_pack_id)
    script_code = allocate_script_code(db, project)

    script = Script(
        project_id=project_id,
        knowledge_pack_id=pack.id if pack else None,
        script_code=script_code,
        title=payload.title,
        description=payload.description,
        status=DEFAULT_SCRIPT_STATUS,
        created_by=creator.id,
    )
    db.add(script)
    try:
        db.flush()
        for definition in initial_document_definitions():
            db.add(
                ScriptDocument(
                    script_id=script.id,
                    document_type=definition.document_type,
                    title=definition.title,
                    content="",
                    position=definition.position,
                )
            )
        from app.services.workflow_service import create_initial_workflow

        create_initial_workflow(
            db,
            script.id,
            actor_user_id=creator.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        record_audit_event(
            db,
            actor_user_id=creator.id,
            action=ACTION_SCRIPT_CREATED,
            entity_type=ENTITY_SCRIPT,
            entity_id=script.id,
            metadata={
                "project_id": str(project_id),
                "script_code": script.script_code,
                "document_count": len(initial_document_definitions()),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to create script due to a conflict.") from exc

    return get_script(db, script.id)


def list_scripts(
    db: Session,
    project_id: UUID,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[Script], int]:
    assert_project_access(db, project_id, user)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = [Script.project_id == project_id]
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in SCRIPT_STATUSES:
            raise ValidationError("Invalid status filter.")
        filters.append(Script.status == cleaned)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            (Script.title.ilike(pattern)) | (Script.script_code.ilike(pattern))
        )

    count_stmt = select(func.count()).select_from(Script)
    list_stmt = select(Script).order_by(Script.created_at.desc(), Script.id.asc())
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return items, total


def update_script(
    db: Session,
    script_id: UUID,
    payload: ScriptUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Script:
    script = get_script_for_user(db, script_id, actor)
    changed: list[str] = []

    if payload.title is not None and payload.title != script.title:
        script.title = payload.title
        changed.append("title")
    if payload.description is not None and payload.description != script.description:
        script.description = payload.description
        changed.append("description")
    if "knowledge_pack_id" in payload.model_fields_set:
        pack = _validate_knowledge_pack(
            db, script.project_id, payload.knowledge_pack_id
        )
        new_id = pack.id if pack else None
        if new_id != script.knowledge_pack_id:
            script.knowledge_pack_id = new_id
            changed.append("knowledge_pack_id")
    if payload.status is not None and payload.status != script.status:
        allowed = SCRIPT_STATUS_TRANSITIONS.get(script.status, frozenset())
        if payload.status not in allowed:
            raise ValidationError(
                f"Cannot transition script status from '{script.status}' "
                f"to '{payload.status}'."
            )
        script.status = payload.status
        changed.append("status")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_SCRIPT_UPDATED,
            entity_type=ENTITY_SCRIPT,
            entity_id=script.id,
            metadata={"changed_fields": changed},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise ConflictError("Unable to update script due to a conflict.") from exc

    return get_script(db, script.id)


def archive_script(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Script:
    """Archive a script. Documents are retained (no physical delete)."""
    script = get_script_for_user(db, script_id, actor)
    if script.status == SCRIPT_STATUS_ARCHIVED:
        return script

    script.status = SCRIPT_STATUS_ARCHIVED
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_SCRIPT_ARCHIVED,
        entity_type=ENTITY_SCRIPT,
        entity_id=script.id,
        metadata={
            "script_code": script.script_code,
            "changed_fields": ["status"],
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    return get_script(db, script.id)


def list_documents(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
) -> list[ScriptDocument]:
    script = get_script_for_user(db, script_id, actor)
    return list(script.documents)


def get_document(
    db: Session,
    script_id: UUID,
    document_type: str,
    *,
    actor: User,
) -> ScriptDocument:
    if document_type not in DOCUMENT_TYPES:
        raise ValidationError("Invalid document type.")
    script = get_script_for_user(db, script_id, actor)
    for document in script.documents:
        if document.document_type == document_type:
            return document
    raise NotFoundError("Script document not found.")


def update_document(
    db: Session,
    script_id: UUID,
    document_type: str,
    payload: ScriptDocumentUpdate,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ScriptDocument:
    document = get_document(db, script_id, document_type, actor=actor)
    changed: list[str] = []

    if payload.title is not None and payload.title != document.title:
        document.title = payload.title
        changed.append("title")
    if payload.content is not None and payload.content != document.content:
        document.content = payload.content
        changed.append("content")

    if changed:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_SCRIPT_DOCUMENT_UPDATED,
            entity_type=ENTITY_SCRIPT,
            entity_id=script_id,
            metadata={
                "document_type": document_type,
                "changed_fields": changed,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        db.refresh(document)
    return document
