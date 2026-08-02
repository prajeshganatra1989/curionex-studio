"""Production Session selection algorithm and continue-engine helpers."""

from __future__ import annotations

from typing import Any

from app.ai.constants import JOB_STATUS_QUEUED, JOB_STATUS_RUNNING
from app.production.stages import ProductionStage

# Session selection buckets (lower = higher priority). Matches product order:
# 1 unfinished, 2 human review, 3 AI generation, 4 quality, 5 version, 6 approval, 7 completed.
SESSION_BUCKET_UNFINISHED = 1
SESSION_BUCKET_HUMAN_REVIEW = 2
SESSION_BUCKET_AI = 3
SESSION_BUCKET_QUALITY = 4
SESSION_BUCKET_VERSION = 5
SESSION_BUCKET_APPROVAL = 6
SESSION_BUCKET_COMPLETED = 7
SESSION_BUCKET_BLOCKED = 0

PRIORITY_RANK = {"A": 0, "B": 1, "C": 2}

TIMELINE_STEPS: tuple[tuple[str, str], ...] = (
    ("editorial_topic", "Editorial Topic"),
    ("knowledge_pack", "Knowledge Pack"),
    ("discovery_brief", "Discovery Brief"),
    ("story_spine", "Story Spine"),
    ("master_script", "Master Script"),
    ("quality_review", "Quality Review"),
    ("version", "Version"),
    ("approval", "Approval"),
)

STAGE_DISPLAY_LABELS: dict[str, str] = {
    "idea": "Idea",
    "research": "Research",
    "discovery_brief": "Discovery Brief Review",
    "story_spine": "Story Spine",
    "master_script": "Master Script",
    "quality_review": "Quality Review",
    "needs_revision": "Needs Revision",
    "ready_for_version": "Ready for Version",
    "version_created": "Version Created",
    "pending_human_review": "Pending Human Review",
    "approved": "Approved",
    "blocked": "Blocked",
    "archived": "Archived",
}

MINUTES_PER_REMAINING_STEP = 12


def session_selection_bucket(stage: ProductionStage, next_action: dict[str, Any], ai_status: str | None) -> int:
    """Map a classified unit into the Production Session priority bucket."""
    code = (next_action or {}).get("code") or ""
    if stage in ("approved", "archived"):
        return SESSION_BUCKET_COMPLETED
    if stage == "blocked" or code in {"resolve_blocker", "configure_ai_provider"}:
        return SESSION_BUCKET_BLOCKED
    if stage == "pending_human_review" or code in {
        "review_approval",
        "open_pending_review",
    }:
        return SESSION_BUCKET_HUMAN_REVIEW
    if code == "submit_human_review":
        return SESSION_BUCKET_APPROVAL
    if (
        ai_status in {JOB_STATUS_QUEUED, JOB_STATUS_RUNNING}
        or code.startswith("generate_")
        or code in {"retry_ai_job"}
    ):
        return SESSION_BUCKET_AI
    if stage == "quality_review" or code in {
        "run_quality_review",
        "open_quality_review",
        "fix_quality_issues",
    }:
        return SESSION_BUCKET_QUALITY
    if stage in {"ready_for_version", "version_created"} or code in {
        "create_version",
        "view_approved_version",
    }:
        return SESSION_BUCKET_VERSION
    return SESSION_BUCKET_UNFINISHED


def build_timeline(
    *,
    has_topic: bool,
    has_knowledge_pack: bool,
    knowledge_pack_complete: bool,
    discovery: bool,
    story: bool,
    master: bool,
    quality_done: bool,
    version_done: bool,
    approval_done: bool,
    stage: str,
) -> list[dict[str, str]]:
    """Return timeline steps with status complete | current | upcoming."""
    complete_flags = {
        "editorial_topic": has_topic or has_knowledge_pack or discovery,
        "knowledge_pack": has_knowledge_pack
        and (knowledge_pack_complete or discovery or story or master),
        "discovery_brief": discovery,
        "story_spine": story,
        "master_script": master,
        "quality_review": quality_done,
        "version": version_done,
        "approval": approval_done,
    }
    if discovery or story or master or quality_done or version_done or approval_done:
        complete_flags["editorial_topic"] = True
        complete_flags["knowledge_pack"] = (
            complete_flags["knowledge_pack"] or has_knowledge_pack
        )
    if story or master or quality_done or version_done or approval_done:
        complete_flags["discovery_brief"] = True
    if master or quality_done or version_done or approval_done:
        complete_flags["story_spine"] = True
    if quality_done or version_done or approval_done:
        complete_flags["master_script"] = True
    if version_done or approval_done:
        complete_flags["quality_review"] = True
    if approval_done:
        complete_flags["version"] = True

    steps: list[dict[str, str]] = []
    current_assigned = False
    for key, label in TIMELINE_STEPS:
        if complete_flags.get(key):
            status = "complete"
        elif not current_assigned:
            status = "current"
            current_assigned = True
        else:
            status = "upcoming"
        steps.append({"key": key, "label": label, "status": status})

    if not current_assigned:
        for step in steps:
            step["status"] = "complete"

    # stage unused for assignment but kept for API evolution / callers
    _ = stage
    return steps


def remaining_steps_from_timeline(timeline: list[dict[str, str]]) -> int:
    return sum(1 for step in timeline if step["status"] != "complete")
