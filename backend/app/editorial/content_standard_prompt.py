"""Format and inject the active Content Standard into AI prompt variables."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.editorial.content_standard_constants import (
    CONTENT_STANDARD_STATUS_ACTIVE,
)
from app.models.content_standard import ContentStandard


def get_active_content_standard(db: Session) -> ContentStandard | None:
    return db.scalars(
        select(ContentStandard).where(
            ContentStandard.status == CONTENT_STANDARD_STATUS_ACTIVE
        )
    ).first()


def format_content_standard(standard: ContentStandard) -> str:
    """Render the standard as a single editorial block for prompt injection."""
    sections = [
        f"# {standard.name} v{standard.version}",
        "",
        "## Mission",
        standard.mission.strip(),
        "",
        "## Target audience",
        standard.target_audience.strip(),
        "",
        "## Brand voice",
        standard.brand_voice.strip(),
        "",
        "## Editorial principles",
        standard.editorial_principles.strip(),
        "",
        "## Hook rules",
        standard.hook_rules.strip(),
        "",
        "## Story structure",
        standard.story_structure.strip(),
        "",
        "## Fact policy",
        standard.fact_policy.strip(),
        "",
        "## Citation policy",
        standard.citation_policy.strip(),
        "",
        "## Tone guidelines",
        standard.tone_guidelines.strip(),
        "",
        "## Language rules",
        standard.language_rules.strip(),
        "",
        "## Forbidden patterns",
        standard.forbidden_patterns.strip(),
        "",
        "## Approved CTA patterns",
        standard.approved_cta_patterns.strip(),
        "",
        "## Quality checklist",
        standard.quality_checklist.strip(),
        "",
        "## Defaults",
        f"- Duration: {standard.default_duration_seconds} seconds",
        f"- Target words: {standard.default_target_words}",
    ]
    return "\n".join(sections).strip()


def content_standard_prompt_variables(
    standard: ContentStandard | None,
) -> dict[str, str]:
    """Build template variables derived from the active Content Standard.

    Always returns keys so templates can safely declare them even when no
    standard is active yet (empty / fallback strings).
    """
    if standard is None:
        return {
            "content_standard": "",
            "content_standard_name": "",
            "content_standard_version": "",
            "content_standard_label": "",
            "brand_voice": "",
            "quality_requirements": "",
            "target_audience": "",
            "story_structure": "",
            "fact_policy": "",
            "tone_guidelines": "",
            "forbidden_patterns": "",
            "approved_cta_patterns": "",
            "default_duration_seconds": "60",
            "default_target_words": "160",
        }

    return {
        "content_standard": format_content_standard(standard),
        "content_standard_name": standard.name.strip(),
        "content_standard_version": standard.version.strip(),
        "content_standard_label": (
            f"{standard.name.strip()} v{standard.version.strip()}"
        ),
        "brand_voice": standard.brand_voice.strip(),
        "quality_requirements": standard.quality_checklist.strip(),
        "target_audience": standard.target_audience.strip(),
        "story_structure": standard.story_structure.strip(),
        "fact_policy": standard.fact_policy.strip(),
        "tone_guidelines": standard.tone_guidelines.strip(),
        "forbidden_patterns": standard.forbidden_patterns.strip(),
        "approved_cta_patterns": standard.approved_cta_patterns.strip(),
        "default_duration_seconds": str(standard.default_duration_seconds),
        "default_target_words": str(standard.default_target_words),
    }


def inject_content_standard_variables(
    db: Session,
    variables: dict[str, Any],
    *,
    overwrite_editorial: bool = True,
) -> dict[str, Any]:
    """Merge active Content Standard fields into a prompt variable map.

    When ``overwrite_editorial`` is True (default), brand_voice and
    quality_requirements are sourced from the Content Standard so prompts do
    not rely on duplicated AI Settings copy.
    """
    standard = get_active_content_standard(db)
    injected = content_standard_prompt_variables(standard)
    merged = dict(variables)
    for key, value in injected.items():
        if key in {"brand_voice", "quality_requirements"} and not overwrite_editorial:
            if key not in merged or not str(merged.get(key) or "").strip():
                merged[key] = value
            continue
        if key.startswith("content_standard") or overwrite_editorial:
            merged[key] = value
        elif key not in merged:
            merged[key] = value
    return merged
