"""Production Session service — guided next-work selection."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.editorial import EditorialTopic
from app.models.user import User
from app.production.session import (
    MINUTES_PER_REMAINING_STEP,
    PRIORITY_RANK,
    SESSION_BUCKET_COMPLETED,
    STAGE_DISPLAY_LABELS,
    build_timeline,
    remaining_steps_from_timeline,
    session_selection_bucket,
)
from app.services import production_service
from app.services.production_service import ClassifiedUnit


def _topics_by_project(db: Session, project_ids: set[UUID]) -> dict[UUID, EditorialTopic]:
    if not project_ids:
        return {}
    rows = db.scalars(
        select(EditorialTopic).where(EditorialTopic.linked_project_id.in_(project_ids))
    ).all()
    return {row.linked_project_id: row for row in rows if row.linked_project_id}


def _unit_sort_key(unit: ClassifiedUnit, topic: EditorialTopic | None) -> tuple:
    bucket = session_selection_bucket(
        unit.stage,
        unit.next_action,
        unit.classification.ai_job.status,
    )
    wave = int(topic.production_wave) if topic is not None else 4
    priority = PRIORITY_RANK.get((topic.priority if topic else "C") or "C", 2)
    project_created = unit.project.created_at or datetime.now(UTC)
    script_created = (
        unit.script.created_at if unit.script is not None else project_created
    )
    return (bucket, wave, priority, project_created, script_created)


def _quality_done(unit: ClassifiedUnit) -> bool:
    quality = unit.classification.quality
    if unit.stage in {
        "ready_for_version",
        "version_created",
        "pending_human_review",
        "approved",
    }:
        return True
    if quality.score is None:
        return False
    if quality.stale:
        return False
    return quality.recommendation in {"ready_for_version", "human_review"} or (
        quality.score >= 80 and not quality.has_critical_issue
    )


def _version_done(unit: ClassifiedUnit) -> bool:
    return unit.stage in {
        "version_created",
        "pending_human_review",
        "approved",
    } or unit.classification.version.version_id is not None


def _approval_done(unit: ClassifiedUnit) -> bool:
    return unit.stage == "approved" or unit.classification.approval.status == "approved"


def _serialize_unit(
    unit: ClassifiedUnit,
    topic: EditorialTopic | None,
    *,
    include_sidebar: bool = False,
) -> dict[str, Any]:
    docs = unit.classification.documents
    timeline = build_timeline(
        has_topic=topic is not None,
        has_knowledge_pack=unit.classification.has_knowledge_pack,
        knowledge_pack_complete=unit.classification.knowledge_pack_complete,
        discovery=docs.discovery_brief,
        story=docs.story_spine,
        master=docs.master_script,
        quality_done=_quality_done(unit),
        version_done=_version_done(unit),
        approval_done=_approval_done(unit),
        stage=unit.stage,
    )
    remaining_steps = remaining_steps_from_timeline(timeline)
    topic_title = topic.title if topic is not None else unit.project.name
    payload: dict[str, Any] = {
        "topic_title": topic_title,
        "topic_id": str(topic.id) if topic is not None else None,
        "topic_slug": topic.slug if topic is not None else None,
        "project_id": str(unit.project.id),
        "project_code": unit.project.project_code,
        "project_name": unit.project.name,
        "script_id": str(unit.script.id) if unit.script else None,
        "script_title": unit.script.title if unit.script else None,
        "production_stage": unit.stage,
        "stage_label": STAGE_DISPLAY_LABELS.get(unit.stage, unit.stage),
        "next_action": unit.next_action,
        "continue_url": unit.next_action.get("href"),
        "wave": int(topic.production_wave) if topic is not None else None,
        "priority": topic.priority if topic is not None else None,
        "estimated_remaining_steps": remaining_steps,
        "timeline": timeline,
    }
    if include_sidebar:
        quality = unit.classification.quality
        approval = unit.classification.approval
        version = unit.classification.version
        payload["sidebar"] = {
            "wave": payload["wave"],
            "priority": payload["priority"],
            "estimated_remaining_minutes": remaining_steps * MINUTES_PER_REMAINING_STEP,
            "quality_score": quality.score,
            "quality_band": quality.band,
            "approval_status": approval.status,
            "knowledge_pack_status": (
                "complete"
                if unit.classification.knowledge_pack_complete
                else ("active" if unit.classification.has_knowledge_pack else "missing")
            ),
            "knowledge_pack_completion": unit.knowledge_pack_completion,
            "version_status": version.version_status,
            "reviewer": None,
        }
    return payload


def _warnings_for_unit(unit: ClassifiedUnit) -> list[str]:
    warnings: list[str] = []
    if unit.stage == "blocked" or unit.next_action.get("blocked"):
        warnings.append(unit.next_action.get("reason") or "Production is blocked.")
    if unit.classification.ai_job.status == "failed":
        err = unit.classification.ai_job.error_message or "Latest AI job failed."
        warnings.append(err)
    if unit.classification.quality.stale:
        warnings.append("Quality review is stale — re-run before versioning.")
    if unit.classification.quality.has_critical_issue:
        warnings.append("Quality review reported critical issues.")
    return warnings


def build_production_session(db: Session, user: User) -> dict[str, Any]:
    """Build the guided Production Session payload for the current user."""
    settings = production_service.get_or_create_settings(db)
    overview = production_service.build_overview(db, user)
    goals = overview["goals"]

    units = production_service._build_classified_units(  # noqa: SLF001
        db, user, include_project_only=True
    )
    project_ids = {unit.project.id for unit in units}
    topics = _topics_by_project(db, project_ids)

    active: list[ClassifiedUnit] = []
    completed: list[ClassifiedUnit] = []
    for unit in units:
        bucket = session_selection_bucket(
            unit.stage,
            unit.next_action,
            unit.classification.ai_job.status,
        )
        if bucket == SESSION_BUCKET_COMPLETED:
            completed.append(unit)
        else:
            active.append(unit)

    active.sort(key=lambda u: _unit_sort_key(u, topics.get(u.project.id)))
    completed.sort(
        key=lambda u: u.updated_at or datetime.now(UTC),
        reverse=True,
    )

    current = active[0] if active else None
    upcoming = active[1:6]
    previous = completed[0] if completed else None

    daily_target = int(goals["daily_target"])
    approved_today = int(goals["approved_today"])
    approved_total = int(goals["approved_total"])
    approved_target = int(goals["approved_target"])
    remaining = int(goals["remaining"])
    completion_percent = float(goals["completion_percent"])

    # Streak architecture placeholder — always 0 until streak tracking ships.
    current_streak = 0

    estimated_finish: str | None = None
    if current is not None:
        topic = topics.get(current.project.id)
        current_payload = _serialize_unit(current, topic, include_sidebar=True)
        minutes = current_payload["sidebar"]["estimated_remaining_minutes"]
        estimated_finish = f"~{minutes} min remaining on current production"
    else:
        current_payload = None

    warnings: list[str] = []
    if current is not None:
        warnings.extend(_warnings_for_unit(current))

    empty = current is None
    return {
        "today": {
            "goal": daily_target,
            "completed": approved_today,
            "estimated_finish": estimated_finish,
            "current_streak": current_streak,
        },
        "progress": {
            "approved_total": approved_total,
            "approved_target": approved_target,
            "remaining": remaining,
            "completion_percent": completion_percent,
            "approved_today": approved_today,
        },
        "current": current_payload,
        "upcoming": [
            _serialize_unit(unit, topics.get(unit.project.id)) for unit in upcoming
        ],
        "previous_completed": (
            {
                "topic_title": (
                    topics[previous.project.id].title
                    if previous.project.id in topics
                    else previous.project.name
                ),
                "stage_label": STAGE_DISPLAY_LABELS.get(previous.stage, previous.stage),
                "project_id": str(previous.project.id),
                "script_id": str(previous.script.id) if previous.script else None,
            }
            if previous is not None
            else None
        ),
        "warnings": warnings,
        "empty": empty,
        "browse_topics_url": "/topics",
        "settings": {
            "daily_approved_script_target": settings.daily_approved_script_target,
            "approved_script_target": settings.approved_script_target,
        },
    }
