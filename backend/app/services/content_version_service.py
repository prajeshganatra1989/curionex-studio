"""Immutable ContentVersion and Approval domain services."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.audit.actions import (
    ACTION_APPROVAL_APPROVED,
    ACTION_APPROVAL_CANCELLED,
    ACTION_APPROVAL_REJECTED,
    ACTION_APPROVAL_REQUESTED,
    ACTION_CONTENT_VERSION_CREATED,
    ENTITY_APPROVAL,
    ENTITY_CONTENT_VERSION,
)
from app.content_versions.constants import (
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_CANCELLED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REJECTED,
    APPROVAL_STATUSES,
    DEFAULT_VERSION_STATUS,
    VERSION_STATUS_APPROVED,
    VERSION_STATUS_ARCHIVED,
    VERSION_STATUS_DRAFT,
    VERSION_STATUS_IN_REVIEW,
    VERSION_STATUS_REJECTED,
    VERSION_STATUSES,
)
from app.models.content_version import Approval, ContentVersion
from app.models.project import Project
from app.models.script import Script
from app.models.user import User
from app.schemas.content_version import (
    ApprovalRequestCreate,
    ApprovalReviewRequest,
    ContentVersionCreate,
)
from app.services import project_service
from app.services.audit_service import record_audit_event


class NotFoundError(Exception):
    """Raised when a version or approval cannot be found."""


class ForbiddenError(Exception):
    """Raised when the user lacks project membership access."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


class ConflictError(Exception):
    """Raised for uniqueness / state conflicts."""


def assert_project_access(db: Session, project_id: UUID, user: User) -> Project:
    """Require project existence and membership (plus route-level permissions)."""
    project = db.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")
    if not project_service.is_project_member(db, project_id, user.id):
        raise ForbiddenError("You do not have access to this project.")
    return project


def _advisory_lock_key(project_id: UUID) -> int:
    """Map a project UUID to a signed 64-bit key for pg_advisory_xact_lock."""
    # Use the first 8 bytes of the UUID as a signed bigint.
    value = int.from_bytes(project_id.bytes[:8], byteorder="big", signed=False)
    if value >= 2**63:
        value -= 2**64
    return value


def allocate_next_version_number(db: Session, project_id: UUID) -> int:
    """Allocate the next per-project version number under a transaction lock.

    Uses ``pg_advisory_xact_lock`` so concurrent creators for the same project
    serialize. Unique ``(project_id, version_number)`` remains the safety net.
    """
    db.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": _advisory_lock_key(project_id)},
    )
    current_max = db.scalar(
        select(func.max(ContentVersion.version_number)).where(
            ContentVersion.project_id == project_id
        )
    )
    return int(current_max or 0) + 1


def get_content_version(db: Session, version_id: UUID) -> ContentVersion:
    version = db.get(ContentVersion, version_id)
    if version is None:
        raise NotFoundError("Content version not found.")
    return version


def get_content_version_for_user(
    db: Session,
    version_id: UUID,
    user: User,
) -> ContentVersion:
    version = get_content_version(db, version_id)
    assert_project_access(db, version.project_id, user)
    return version


def _resolve_script_for_project(
    db: Session,
    project_id: UUID,
    script_id: UUID | None,
) -> UUID | None:
    """Validate optional script_id belongs to the same project."""
    if script_id is None:
        return None
    script = db.get(Script, script_id)
    if script is None:
        raise ValidationError("Script not found.")
    if script.project_id != project_id:
        raise ValidationError("Script must belong to the same project.")
    return script.id


def create_content_version(
    db: Session,
    project_id: UUID,
    payload: ContentVersionCreate,
    *,
    creator: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = True,
    script_id: UUID | None = None,
) -> ContentVersion:
    assert_project_access(db, project_id, creator)
    resolved_script_id = _resolve_script_for_project(
        db,
        project_id,
        script_id if script_id is not None else payload.script_id,
    )
    version_number = allocate_next_version_number(db, project_id)
    version = ContentVersion(
        project_id=project_id,
        script_id=resolved_script_id,
        version_number=version_number,
        status=DEFAULT_VERSION_STATUS,
        title=payload.title,
        content=payload.content,
        created_by=creator.id,
    )
    db.add(version)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=creator.id,
            action=ACTION_CONTENT_VERSION_CREATED,
            entity_type=ENTITY_CONTENT_VERSION,
            entity_id=version.id,
            metadata={
                "project_id": str(project_id),
                "script_id": str(resolved_script_id) if resolved_script_id else None,
                "version_number": version.version_number,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if commit:
            db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(
            "Unable to create content version due to a conflict."
        ) from exc
    if commit:
        db.refresh(version)
    return version


def create_version_from_existing(
    db: Session,
    source_version_id: UUID,
    *,
    creator: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentVersion:
    source = get_content_version_for_user(db, source_version_id, creator)
    return create_content_version(
        db,
        source.project_id,
        ContentVersionCreate(
            title=source.title,
            content=source.content,
            script_id=source.script_id,
        ),
        creator=creator,
        ip_address=ip_address,
        user_agent=user_agent,
        script_id=source.script_id,
    )


def list_content_versions(
    db: Session,
    project_id: UUID,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[ContentVersion], int]:
    assert_project_access(db, project_id, user)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = [ContentVersion.project_id == project_id]
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in VERSION_STATUSES:
            raise ValidationError("Invalid status filter.")
        filters.append(ContentVersion.status == cleaned)

    count_stmt = select(func.count()).select_from(ContentVersion)
    list_stmt = select(ContentVersion).order_by(
        ContentVersion.version_number.desc(),
        ContentVersion.id.asc(),
    )
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return items, total


def get_latest_version(
    db: Session,
    project_id: UUID,
    *,
    user: User,
) -> ContentVersion:
    assert_project_access(db, project_id, user)
    version = db.scalar(
        select(ContentVersion)
        .where(ContentVersion.project_id == project_id)
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise NotFoundError("No content versions found for this project.")
    return version


def get_latest_approved_version(
    db: Session,
    project_id: UUID,
    *,
    user: User,
) -> ContentVersion:
    assert_project_access(db, project_id, user)
    version = db.scalar(
        select(ContentVersion)
        .where(
            ContentVersion.project_id == project_id,
            ContentVersion.status == VERSION_STATUS_APPROVED,
        )
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise NotFoundError("No approved content version found for this project.")
    return version


def list_script_content_versions(
    db: Session,
    script_id: UUID,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[ContentVersion], int]:
    script = db.get(Script, script_id)
    if script is None:
        raise NotFoundError("Script not found.")
    assert_project_access(db, script.project_id, user)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = [ContentVersion.script_id == script_id]
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in VERSION_STATUSES:
            raise ValidationError("Invalid status filter.")
        filters.append(ContentVersion.status == cleaned)

    count_stmt = select(func.count()).select_from(ContentVersion)
    list_stmt = select(ContentVersion).order_by(
        ContentVersion.version_number.desc(),
        ContentVersion.id.asc(),
    )
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = int(db.scalar(count_stmt) or 0)
    items = list(
        db.scalars(list_stmt.offset((page - 1) * page_size).limit(page_size)).all()
    )
    return items, total


def get_script_latest_version(
    db: Session,
    script_id: UUID,
    *,
    user: User,
) -> ContentVersion:
    script = db.get(Script, script_id)
    if script is None:
        raise NotFoundError("Script not found.")
    assert_project_access(db, script.project_id, user)
    version = db.scalar(
        select(ContentVersion)
        .where(ContentVersion.script_id == script_id)
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise NotFoundError("No content versions found for this script.")
    return version


def get_script_approved_version(
    db: Session,
    script_id: UUID,
    *,
    user: User,
) -> ContentVersion:
    script = db.get(Script, script_id)
    if script is None:
        raise NotFoundError("Script not found.")
    assert_project_access(db, script.project_id, user)
    version = db.scalar(
        select(ContentVersion)
        .where(
            ContentVersion.script_id == script_id,
            ContentVersion.status == VERSION_STATUS_APPROVED,
        )
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    if version is None:
        raise NotFoundError("No approved content version found for this script.")
    return version


def list_approvals(
    db: Session,
    *,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    project_id: UUID | None = None,
    search: str | None = None,
) -> tuple[list[Approval], int]:
    """List approvals for projects the user can access."""
    from app.models.project import Project as ProjectModel
    from app.models.project import ProjectMember

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    member_project_ids = select(ProjectMember.project_id).where(
        ProjectMember.user_id == user.id
    )

    filters = [ContentVersion.project_id.in_(member_project_ids)]
    if project_id is not None:
        assert_project_access(db, project_id, user)
        filters.append(ContentVersion.project_id == project_id)
    if status is not None:
        cleaned = status.strip().lower()
        if cleaned not in APPROVAL_STATUSES:
            raise ValidationError("Invalid approval status filter.")
        filters.append(Approval.status == cleaned)
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                ProjectModel.project_code.ilike(term),
                Script.script_code.ilike(term),
                Script.title.ilike(term),
                ContentVersion.title.ilike(term),
            )
        )

    base = (
        select(Approval)
        .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
        .join(ProjectModel, ContentVersion.project_id == ProjectModel.id)
        .outerjoin(Script, ContentVersion.script_id == Script.id)
    )
    count_base = (
        select(func.count())
        .select_from(Approval)
        .join(ContentVersion, Approval.content_version_id == ContentVersion.id)
        .join(ProjectModel, ContentVersion.project_id == ProjectModel.id)
        .outerjoin(Script, ContentVersion.script_id == Script.id)
    )
    for condition in filters:
        base = base.where(condition)
        count_base = count_base.where(condition)

    total = int(db.scalar(count_base) or 0)
    items = list(
        db.scalars(
            base.options(
                joinedload(Approval.requester),
                joinedload(Approval.reviewer),
                joinedload(Approval.content_version).joinedload(ContentVersion.project),
                joinedload(Approval.content_version).joinedload(ContentVersion.script),
            )
            .order_by(Approval.created_at.desc(), Approval.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).unique().all()
    )
    return items, total


def list_approvals_for_version(
    db: Session,
    version_id: UUID,
    *,
    user: User,
) -> list[Approval]:
    get_content_version_for_user(db, version_id, user)
    return list(
        db.scalars(
            select(Approval)
            .where(Approval.content_version_id == version_id)
            .order_by(Approval.created_at.asc())
        ).all()
    )


def get_approval_for_user(db: Session, approval_id: UUID, user: User) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise NotFoundError("Approval not found.")
    get_content_version_for_user(db, approval.content_version_id, user)
    return approval


def request_approval(
    db: Session,
    version_id: UUID,
    payload: ApprovalRequestCreate,
    *,
    requester: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = True,
) -> Approval:
    version = get_content_version_for_user(db, version_id, requester)
    if version.status == VERSION_STATUS_ARCHIVED:
        raise ValidationError("Cannot request approval for an archived version.")
    if version.status == VERSION_STATUS_APPROVED:
        raise ValidationError("Version is already approved.")

    existing = db.scalar(
        select(Approval).where(
            Approval.content_version_id == version_id,
            Approval.status == APPROVAL_STATUS_PENDING,
        )
    )
    if existing is not None:
        raise ConflictError("A pending approval already exists for this version.")

    approval = Approval(
        content_version_id=version.id,
        requested_by=requester.id,
        status=APPROVAL_STATUS_PENDING,
        comment=payload.comment,
    )
    version.status = VERSION_STATUS_IN_REVIEW
    db.add(approval)
    try:
        db.flush()
        record_audit_event(
            db,
            actor_user_id=requester.id,
            action=ACTION_APPROVAL_REQUESTED,
            entity_type=ENTITY_APPROVAL,
            entity_id=approval.id,
            metadata={
                "content_version_id": str(version.id),
                "version_number": version.version_number,
                "status": APPROVAL_STATUS_PENDING,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if commit:
            db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("A pending approval already exists for this version.") from exc
    if commit:
        db.refresh(approval)
    return approval


def _review_approval(
    db: Session,
    approval_id: UUID,
    *,
    reviewer: User,
    new_status: str,
    version_status: str,
    audit_action: str,
    payload: ApprovalReviewRequest,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Approval:
    approval = get_approval_for_user(db, approval_id, reviewer)
    if approval.status != APPROVAL_STATUS_PENDING:
        raise ConflictError("Only pending approvals can be reviewed.")

    version = get_content_version(db, approval.content_version_id)
    if version.status == VERSION_STATUS_ARCHIVED:
        raise ValidationError("Cannot review an approval for an archived version.")

    approval.status = new_status
    approval.reviewed_by = reviewer.id
    approval.reviewed_at = datetime.now(UTC)
    if payload.comment is not None:
        approval.comment = payload.comment
    version.status = version_status

    record_audit_event(
        db,
        actor_user_id=reviewer.id,
        action=audit_action,
        entity_type=ENTITY_APPROVAL,
        entity_id=approval.id,
        metadata={
            "content_version_id": str(version.id),
            "version_number": version.version_number,
            "status": new_status,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Orchestrate linked ContentWorkflow when present (M2I). Preserve M2G if none.
    from app.services import workflow_service

    if new_status == APPROVAL_STATUS_APPROVED:
        workflow_service.sync_workflow_after_approval_decision(
            db,
            content_version_id=version.id,
            approved=True,
            actor=reviewer,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    elif new_status == APPROVAL_STATUS_REJECTED:
        workflow_service.sync_workflow_after_approval_decision(
            db,
            content_version_id=version.id,
            approved=False,
            actor=reviewer,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    db.commit()
    db.refresh(approval)
    return approval


def approve_approval(
    db: Session,
    approval_id: UUID,
    payload: ApprovalReviewRequest,
    *,
    reviewer: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Approval:
    return _review_approval(
        db,
        approval_id,
        reviewer=reviewer,
        new_status=APPROVAL_STATUS_APPROVED,
        version_status=VERSION_STATUS_APPROVED,
        audit_action=ACTION_APPROVAL_APPROVED,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def reject_approval(
    db: Session,
    approval_id: UUID,
    payload: ApprovalReviewRequest,
    *,
    reviewer: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Approval:
    if not payload.comment or not payload.comment.strip():
        raise ValidationError("A rejection reason is required.")
    return _review_approval(
        db,
        approval_id,
        reviewer=reviewer,
        new_status=APPROVAL_STATUS_REJECTED,
        version_status=VERSION_STATUS_REJECTED,
        audit_action=ACTION_APPROVAL_REJECTED,
        payload=payload,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def cancel_approval(
    db: Session,
    approval_id: UUID,
    payload: ApprovalReviewRequest,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Approval:
    """Cancel a pending approval; version returns to draft if still in review."""
    approval = get_approval_for_user(db, approval_id, actor)
    if approval.status != APPROVAL_STATUS_PENDING:
        raise ConflictError("Only pending approvals can be cancelled.")

    version = get_content_version(db, approval.content_version_id)
    approval.status = APPROVAL_STATUS_CANCELLED
    approval.reviewed_by = actor.id
    approval.reviewed_at = datetime.now(UTC)
    if payload.comment is not None:
        approval.comment = payload.comment
    if version.status == VERSION_STATUS_IN_REVIEW:
        version.status = VERSION_STATUS_DRAFT

    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_APPROVAL_CANCELLED,
        entity_type=ENTITY_APPROVAL,
        entity_id=approval.id,
        metadata={
            "content_version_id": str(version.id),
            "version_number": version.version_number,
            "status": APPROVAL_STATUS_CANCELLED,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.commit()
    db.refresh(approval)
    return approval
