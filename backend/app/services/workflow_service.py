"""Content production workflow orchestration services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.audit.actions import (
    ACTION_WORKFLOW_ARCHIVED,
    ACTION_WORKFLOW_COMPLETED,
    ACTION_WORKFLOW_CREATED,
    ACTION_WORKFLOW_RETURNED_TO_WORKSPACE,
    ACTION_WORKFLOW_REVIEW_SUBMITTED,
    ACTION_WORKFLOW_STAGE_CHANGED,
    ACTION_WORKFLOW_VERSION_CREATED,
    ENTITY_WORKFLOW,
)
from app.content_versions.constants import (
    APPROVAL_STATUS_APPROVED,
    APPROVAL_STATUS_PENDING,
    APPROVAL_STATUS_REJECTED,
    VERSION_STATUS_APPROVED,
    VERSION_STATUS_DRAFT,
    VERSION_STATUS_IN_REVIEW,
)
from app.models.content_version import Approval, ContentVersion
from app.models.script import Script
from app.models.user import User
from app.models.workflow import ContentWorkflow
from app.schemas.content_version import ApprovalRequestCreate, ContentVersionCreate
from app.scripts.catalog import DOCUMENT_TYPES
from app.services import content_version_service, script_service
from app.services.audit_service import record_audit_event
from app.workflows.constants import (
    ARCHIVEABLE_STAGES,
    DEFAULT_WORKFLOW_STAGE,
    DEFAULT_WORKFLOW_STATUS,
    WORKFLOW_STAGE_COMPLETED,
    WORKFLOW_STAGE_REVIEW,
    WORKFLOW_STAGE_TRANSITIONS,
    WORKFLOW_STAGE_VERSIONING,
    WORKFLOW_STAGE_WORKSPACE,
    WORKFLOW_STATUS_ACTIVE,
    WORKFLOW_STATUS_ARCHIVED,
    WORKFLOW_STATUS_COMPLETED,
)
from app.workflows.snapshot import SnapshotValidationError, build_workspace_snapshot

# Distinct from content versions (1) and scripts (2).
_WORKFLOW_LOCK_NAMESPACE = 3


class NotFoundError(Exception):
    """Raised when a workflow cannot be found."""


class ForbiddenError(Exception):
    """Raised when the user lacks project membership access."""


class ValidationError(Exception):
    """Raised for domain validation failures."""


class ConflictError(Exception):
    """Raised for uniqueness / state conflicts."""


def _advisory_obj_key(script_id: UUID) -> int:
    value = int.from_bytes(script_id.bytes[:4], byteorder="big", signed=False)
    if value >= 2**31:
        value -= 2**32
    return value


def _lock_workflow(db: Session, script_id: UUID) -> None:
    db.execute(
        text("SELECT pg_advisory_xact_lock(:ns, :key)"),
        {"ns": _WORKFLOW_LOCK_NAMESPACE, "key": _advisory_obj_key(script_id)},
    )


def create_initial_workflow(
    db: Session,
    script_id: UUID,
    *,
    actor_user_id: UUID,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentWorkflow:
    """Create the default ContentWorkflow for a new Script (flush only)."""
    workflow = ContentWorkflow(
        script_id=script_id,
        current_stage=DEFAULT_WORKFLOW_STAGE,
        status=DEFAULT_WORKFLOW_STATUS,
        active_content_version_id=None,
    )
    db.add(workflow)
    db.flush()
    record_audit_event(
        db,
        actor_user_id=actor_user_id,
        action=ACTION_WORKFLOW_CREATED,
        entity_type=ENTITY_WORKFLOW,
        entity_id=workflow.id,
        metadata={
            "script_id": str(script_id),
            "current_stage": workflow.current_stage,
            "status": workflow.status,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return workflow


def get_workflow_by_script_id(db: Session, script_id: UUID) -> ContentWorkflow:
    workflow = db.scalar(
        select(ContentWorkflow)
        .where(ContentWorkflow.script_id == script_id)
        .options(selectinload(ContentWorkflow.active_content_version))
    )
    if workflow is None:
        raise NotFoundError("Workflow not found.")
    return workflow


def get_workflow_for_user(
    db: Session,
    script_id: UUID,
    user: User,
) -> tuple[ContentWorkflow, Script]:
    try:
        script = script_service.get_script_for_user(db, script_id, user)
    except script_service.NotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except script_service.ForbiddenError as exc:
        raise ForbiddenError(str(exc)) from exc
    workflow = get_workflow_by_script_id(db, script_id)
    return workflow, script


def get_workflow_by_active_version(
    db: Session,
    content_version_id: UUID,
) -> ContentWorkflow | None:
    return db.scalar(
        select(ContentWorkflow).where(
            ContentWorkflow.active_content_version_id == content_version_id
        )
    )


def _assert_workflow_mutable(workflow: ContentWorkflow) -> None:
    if workflow.status == WORKFLOW_STATUS_ARCHIVED:
        raise ValidationError("Archived workflows cannot be modified.")
    if workflow.status == WORKFLOW_STATUS_COMPLETED and workflow.current_stage == (
        WORKFLOW_STAGE_COMPLETED
    ):
        raise ValidationError("Completed workflows cannot be modified.")


def _required_documents_present(script: Script) -> bool:
    present = {doc.document_type for doc in script.documents}
    return DOCUMENT_TYPES.issubset(present)


def _set_stage(
    db: Session,
    workflow: ContentWorkflow,
    *,
    to_stage: str,
    actor: User,
    ip_address: str | None,
    user_agent: str | None,
    extra_metadata: dict | None = None,
) -> None:
    from_stage = workflow.current_stage
    if from_stage == to_stage:
        return
    workflow.current_stage = to_stage
    metadata = {
        "from_stage": from_stage,
        "to_stage": to_stage,
        "script_id": str(workflow.script_id),
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_WORKFLOW_STAGE_CHANGED,
        entity_type=ENTITY_WORKFLOW,
        entity_id=workflow.id,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def sync_workflow_after_approval_decision(
    db: Session,
    *,
    content_version_id: UUID,
    approved: bool,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentWorkflow | None:
    """Update workflow after M2G approve/reject. No-op if no linked workflow."""
    workflow = get_workflow_by_active_version(db, content_version_id)
    if workflow is None:
        return None
    if workflow.status == WORKFLOW_STATUS_ARCHIVED:
        return workflow

    _lock_workflow(db, workflow.script_id)
    # Re-read under lock
    workflow = get_workflow_by_active_version(db, content_version_id)
    if workflow is None:
        return None

    if approved:
        from_stage = workflow.current_stage
        workflow.current_stage = WORKFLOW_STAGE_COMPLETED
        workflow.status = WORKFLOW_STATUS_COMPLETED
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_WORKFLOW_COMPLETED,
            entity_type=ENTITY_WORKFLOW,
            entity_id=workflow.id,
            metadata={
                "from_stage": from_stage,
                "to_stage": WORKFLOW_STAGE_COMPLETED,
                "content_version_id": str(content_version_id),
                "script_id": str(workflow.script_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if from_stage != WORKFLOW_STAGE_COMPLETED:
            record_audit_event(
                db,
                actor_user_id=actor.id,
                action=ACTION_WORKFLOW_STAGE_CHANGED,
                entity_type=ENTITY_WORKFLOW,
                entity_id=workflow.id,
                metadata={
                    "from_stage": from_stage,
                    "to_stage": WORKFLOW_STAGE_COMPLETED,
                    "script_id": str(workflow.script_id),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
    else:
        from_stage = workflow.current_stage
        workflow.current_stage = WORKFLOW_STAGE_WORKSPACE
        workflow.status = WORKFLOW_STATUS_ACTIVE
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_WORKFLOW_RETURNED_TO_WORKSPACE,
            entity_type=ENTITY_WORKFLOW,
            entity_id=workflow.id,
            metadata={
                "from_stage": from_stage,
                "to_stage": WORKFLOW_STAGE_WORKSPACE,
                "content_version_id": str(content_version_id),
                "script_id": str(workflow.script_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        if from_stage != WORKFLOW_STAGE_WORKSPACE:
            record_audit_event(
                db,
                actor_user_id=actor.id,
                action=ACTION_WORKFLOW_STAGE_CHANGED,
                entity_type=ENTITY_WORKFLOW,
                entity_id=workflow.id,
                metadata={
                    "from_stage": from_stage,
                    "to_stage": WORKFLOW_STAGE_WORKSPACE,
                    "script_id": str(workflow.script_id),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
    return workflow


def get_workflow_detail(
    db: Session,
    script_id: UUID,
    *,
    user: User,
) -> tuple[ContentWorkflow, Script, Approval | None]:
    workflow, script = get_workflow_for_user(db, script_id, user)
    latest_approval = None
    if workflow.active_content_version_id is not None:
        latest_approval = db.scalar(
            select(Approval)
            .where(
                Approval.content_version_id == workflow.active_content_version_id
            )
            .order_by(Approval.created_at.desc())
            .limit(1)
        )
    return workflow, script, latest_approval


def _version_ref(version: ContentVersion | None) -> ContentVersion | None:
    return version


def get_workflow_status(
    db: Session,
    script_id: UUID,
    *,
    user: User,
) -> dict:
    workflow, script = get_workflow_for_user(db, script_id, user)
    project_id = script.project_id

    latest = db.scalar(
        select(ContentVersion)
        .where(ContentVersion.project_id == project_id)
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    approved = db.scalar(
        select(ContentVersion)
        .where(
            ContentVersion.project_id == project_id,
            ContentVersion.status == VERSION_STATUS_APPROVED,
        )
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )
    active = None
    if workflow.active_content_version_id is not None:
        active = db.get(ContentVersion, workflow.active_content_version_id)

    pending = None
    if workflow.active_content_version_id is not None:
        pending = db.scalar(
            select(Approval).where(
                Approval.content_version_id == workflow.active_content_version_id,
                Approval.status == APPROVAL_STATUS_PENDING,
            )
        )

    return {
        "script_id": script_id,
        "stage": workflow.current_stage,
        "status": workflow.status,
        "active_version": _version_ref(active),
        "latest_version": _version_ref(latest),
        "approved_version": _version_ref(approved),
        "pending_approval": pending,
    }


def create_version_from_workspace(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[ContentWorkflow, ContentVersion]:
    workflow, script = get_workflow_for_user(db, script_id, actor)
    _assert_workflow_mutable(workflow)
    if workflow.current_stage not in {
        WORKFLOW_STAGE_WORKSPACE,
        WORKFLOW_STAGE_VERSIONING,
    }:
        raise ValidationError(
            "Versions can only be created from workspace or versioning stages."
        )
    if not _required_documents_present(script):
        raise ValidationError("Required workspace documents are missing.")

    _lock_workflow(db, script_id)
    workflow = get_workflow_by_script_id(db, script_id)

    try:
        snapshot = build_workspace_snapshot(script.documents)
    except SnapshotValidationError as exc:
        raise ValidationError(str(exc)) from exc

    version = content_version_service.create_content_version(
        db,
        script.project_id,
        ContentVersionCreate(
            title=f"{script.script_code} — {script.title}",
            content=snapshot,
            script_id=script.id,
        ),
        creator=actor,
        ip_address=ip_address,
        user_agent=user_agent,
        commit=False,
        script_id=script.id,
    )

    from_stage = workflow.current_stage
    workflow.active_content_version_id = version.id
    script.content_version_id = version.id
    workflow.current_stage = WORKFLOW_STAGE_VERSIONING
    workflow.status = WORKFLOW_STATUS_ACTIVE

    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_WORKFLOW_VERSION_CREATED,
        entity_type=ENTITY_WORKFLOW,
        entity_id=workflow.id,
        metadata={
            "content_version_id": str(version.id),
            "version_number": version.version_number,
            "script_id": str(script_id),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if from_stage != WORKFLOW_STAGE_VERSIONING:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_WORKFLOW_STAGE_CHANGED,
            entity_type=ENTITY_WORKFLOW,
            entity_id=workflow.id,
            metadata={
                "from_stage": from_stage,
                "to_stage": WORKFLOW_STAGE_VERSIONING,
                "script_id": str(script_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to create workflow version due to a conflict.") from exc

    workflow = get_workflow_by_script_id(db, script_id)
    version = content_version_service.get_content_version(db, version.id)
    return workflow, version


def submit_review(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
    comment: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> tuple[ContentWorkflow, Approval, ContentVersion]:
    workflow, script = get_workflow_for_user(db, script_id, actor)
    _assert_workflow_mutable(workflow)
    if workflow.current_stage != WORKFLOW_STAGE_VERSIONING:
        raise ValidationError("Review can only be submitted from the versioning stage.")
    if workflow.active_content_version_id is None:
        raise ValidationError("An active content version is required to submit review.")

    _lock_workflow(db, script_id)
    workflow = get_workflow_by_script_id(db, script_id)
    version = content_version_service.get_content_version(
        db, workflow.active_content_version_id
    )
    if version.project_id != script.project_id:
        raise ValidationError("Active content version must belong to the same project.")
    if version.status not in {VERSION_STATUS_DRAFT, VERSION_STATUS_IN_REVIEW}:
        raise ValidationError(
            "Active content version must be draft (or already in review) to submit."
        )

    approval = content_version_service.request_approval(
        db,
        version.id,
        ApprovalRequestCreate(comment=comment),
        requester=actor,
        ip_address=ip_address,
        user_agent=user_agent,
        commit=False,
    )

    from_stage = workflow.current_stage
    workflow.current_stage = WORKFLOW_STAGE_REVIEW
    workflow.status = WORKFLOW_STATUS_ACTIVE
    workflow.active_content_version_id = version.id

    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_WORKFLOW_REVIEW_SUBMITTED,
        entity_type=ENTITY_WORKFLOW,
        entity_id=workflow.id,
        metadata={
            "content_version_id": str(version.id),
            "approval_id": str(approval.id),
            "script_id": str(script_id),
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if from_stage != WORKFLOW_STAGE_REVIEW:
        record_audit_event(
            db,
            actor_user_id=actor.id,
            action=ACTION_WORKFLOW_STAGE_CHANGED,
            entity_type=ENTITY_WORKFLOW,
            entity_id=workflow.id,
            metadata={
                "from_stage": from_stage,
                "to_stage": WORKFLOW_STAGE_REVIEW,
                "script_id": str(script_id),
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to submit review due to a conflict.") from exc

    workflow = get_workflow_by_script_id(db, script_id)
    approval = content_version_service.get_approval_for_user(db, approval.id, actor)
    version = content_version_service.get_content_version(db, version.id)
    return workflow, approval, version


def transition_workflow(
    db: Session,
    script_id: UUID,
    target_stage: str,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentWorkflow:
    workflow, script = get_workflow_for_user(db, script_id, actor)
    _assert_workflow_mutable(workflow)

    allowed = WORKFLOW_STAGE_TRANSITIONS.get(workflow.current_stage, frozenset())
    if target_stage not in allowed:
        raise ValidationError(
            f"Cannot transition workflow from '{workflow.current_stage}' "
            f"to '{target_stage}'."
        )

    _lock_workflow(db, script_id)
    workflow = get_workflow_by_script_id(db, script_id)

    if (
        workflow.current_stage == WORKFLOW_STAGE_WORKSPACE
        and target_stage == WORKFLOW_STAGE_VERSIONING
    ):
        if not _required_documents_present(script):
            raise ValidationError("Required workspace documents are missing.")
        _set_stage(
            db,
            workflow,
            to_stage=WORKFLOW_STAGE_VERSIONING,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        workflow.status = WORKFLOW_STATUS_ACTIVE

    elif (
        workflow.current_stage == WORKFLOW_STAGE_VERSIONING
        and target_stage == WORKFLOW_STAGE_REVIEW
    ):
        # Prefer submit-review; transition reuses the same orchestration.
        _, _, _ = submit_review(
            db,
            script_id,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return get_workflow_by_script_id(db, script_id)

    elif (
        workflow.current_stage == WORKFLOW_STAGE_REVIEW
        and target_stage == WORKFLOW_STAGE_COMPLETED
    ):
        if workflow.active_content_version_id is None:
            raise ValidationError("An active content version is required.")
        version = content_version_service.get_content_version(
            db, workflow.active_content_version_id
        )
        approval = db.scalar(
            select(Approval).where(
                Approval.content_version_id == version.id,
                Approval.status == APPROVAL_STATUS_APPROVED,
            )
        )
        if approval is None or version.status != VERSION_STATUS_APPROVED:
            raise ValidationError(
                "Workflow can only complete when the active version is approved."
            )
        sync_workflow_after_approval_decision(
            db,
            content_version_id=version.id,
            approved=True,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    elif (
        workflow.current_stage == WORKFLOW_STAGE_REVIEW
        and target_stage == WORKFLOW_STAGE_WORKSPACE
    ):
        if workflow.active_content_version_id is None:
            raise ValidationError("An active content version is required.")
        version = content_version_service.get_content_version(
            db, workflow.active_content_version_id
        )
        rejected = db.scalar(
            select(Approval).where(
                Approval.content_version_id == version.id,
                Approval.status == APPROVAL_STATUS_REJECTED,
            )
        )
        if rejected is None:
            raise ValidationError(
                "Workflow can only return to workspace after rejection."
            )
        sync_workflow_after_approval_decision(
            db,
            content_version_id=version.id,
            approved=False,
            actor=actor,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    else:
        raise ValidationError("Unsupported workflow transition.")

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to transition workflow due to a conflict.") from exc

    return get_workflow_by_script_id(db, script_id)


def archive_workflow(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ContentWorkflow:
    workflow, _script = get_workflow_for_user(db, script_id, actor)
    if workflow.status == WORKFLOW_STATUS_ARCHIVED:
        return workflow
    if workflow.current_stage not in ARCHIVEABLE_STAGES:
        raise ValidationError(
            "Only workspace, versioning, or review workflows can be archived."
        )

    _lock_workflow(db, script_id)
    workflow = get_workflow_by_script_id(db, script_id)
    workflow.status = WORKFLOW_STATUS_ARCHIVED
    record_audit_event(
        db,
        actor_user_id=actor.id,
        action=ACTION_WORKFLOW_ARCHIVED,
        entity_type=ENTITY_WORKFLOW,
        entity_id=workflow.id,
        metadata={
            "script_id": str(script_id),
            "current_stage": workflow.current_stage,
            "status": WORKFLOW_STATUS_ARCHIVED,
        },
        ip_address=ip_address,
        user_agent=user_agent,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("Unable to archive workflow due to a conflict.") from exc
    return get_workflow_by_script_id(db, script_id)
