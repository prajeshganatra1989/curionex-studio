"""Script document AI draft purposes, schemas, conversion, and fingerprints."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PURPOSE_DISCOVERY_BRIEF = "script.discovery_brief.draft"
PURPOSE_STORY_SPINE = "script.story_spine.draft"
PURPOSE_MASTER_SCRIPT = "script.master_script.draft"

SCRIPT_DRAFT_PURPOSES: frozenset[str] = frozenset(
    {
        PURPOSE_DISCOVERY_BRIEF,
        PURPOSE_STORY_SPINE,
        PURPOSE_MASTER_SCRIPT,
    }
)

DOCUMENT_TYPE_BY_PURPOSE: dict[str, str] = {
    PURPOSE_DISCOVERY_BRIEF: "discovery_brief",
    PURPOSE_STORY_SPINE: "story_spine",
    PURPOSE_MASTER_SCRIPT: "master_script",
}

PURPOSE_BY_DOCUMENT_TYPE: dict[str, str] = {
    v: k for k, v in DOCUMENT_TYPE_BY_PURPOSE.items()
}

ConflictStrategy = Literal["reject_if_non_empty", "replace", "append"]
DEFAULT_CONFLICT_STRATEGY: ConflictStrategy = "reject_if_non_empty"

# Duration / narration controls (centralized — not hard-coded in adapters).
DEFAULT_TARGET_DURATION_SECONDS = 60
DEFAULT_TARGET_WORDS_PER_MINUTE = 150
DURATION_WORD_COUNT_TOLERANCE = 0.10  # ±10%
MASTER_SCRIPT_MAX_REPAIR_ATTEMPTS = 1

DEFAULT_BRAND_VOICE = (
    "curious, clear, cinematic, intelligent, warm, concise, "
    "non-sensational, accessible to a broad audience, evidence-conscious, "
    "optimized for spoken narration"
)

DEFAULT_QUALITY_REQUIREMENTS = (
    "One clear core idea; strong opening; meaningful payoff; factual caution; "
    "no invented certainty; no filler; no unsupported quotation; "
    "no unnecessary jargon; suitable for spoken English; "
    "appropriate for short-form education."
)


def content_fingerprint(text: str) -> str:
    normalized = (text or "").strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def target_word_range(
    *,
    target_duration_seconds: int,
    target_words_per_minute: int,
    tolerance: float = DURATION_WORD_COUNT_TOLERANCE,
) -> tuple[int, int, int]:
    target = max(
        1,
        int(round((target_duration_seconds / 60.0) * target_words_per_minute)),
    )
    lo = max(1, int(round(target * (1.0 - tolerance))))
    hi = int(round(target * (1.0 + tolerance)))
    return lo, target, hi


# --- Discovery Brief ---------------------------------------------------------


class DiscoveryBriefDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str = ""
    working_title: str = ""
    core_question: str = ""
    viewer_promise: str = ""
    target_audience: str = ""
    core_takeaway: str = ""
    content_angle: str = ""
    key_facts: list[str] = Field(default_factory=list)
    claims_requiring_verification: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)
    emotional_direction: str = ""
    visual_opportunities: list[str] = Field(default_factory=list)
    risks_and_cautions: list[str] = Field(default_factory=list)
    recommended_duration_seconds: int = 60

    @field_validator(
        "topic",
        "working_title",
        "core_question",
        "viewer_promise",
        "target_audience",
        "core_takeaway",
        "content_angle",
        "emotional_direction",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator(
        "key_facts",
        "claims_requiring_verification",
        "source_notes",
        "visual_opportunities",
        "risks_and_cautions",
    )
    @classmethod
    def strip_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if str(item).strip()]


def discovery_brief_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "topic": {"type": "string"},
            "working_title": {"type": "string"},
            "core_question": {"type": "string"},
            "viewer_promise": {"type": "string"},
            "target_audience": {"type": "string"},
            "core_takeaway": {"type": "string"},
            "content_angle": {"type": "string"},
            "key_facts": {"type": "array", "items": {"type": "string"}},
            "claims_requiring_verification": {
                "type": "array",
                "items": {"type": "string"},
            },
            "source_notes": {"type": "array", "items": {"type": "string"}},
            "emotional_direction": {"type": "string"},
            "visual_opportunities": {"type": "array", "items": {"type": "string"}},
            "risks_and_cautions": {"type": "array", "items": {"type": "string"}},
            "recommended_duration_seconds": {"type": "integer"},
        },
        "required": [
            "topic",
            "working_title",
            "core_question",
            "viewer_promise",
            "target_audience",
            "core_takeaway",
            "content_angle",
            "key_facts",
            "claims_requiring_verification",
            "source_notes",
            "emotional_direction",
            "visual_opportunities",
            "risks_and_cautions",
            "recommended_duration_seconds",
        ],
    }


def parse_discovery_brief(payload: Any) -> DiscoveryBriefDraft:
    if isinstance(payload, str):
        payload = json.loads(payload)
    return DiscoveryBriefDraft.model_validate(payload)


def discovery_brief_to_plain_text(draft: DiscoveryBriefDraft) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- (none)"

    return "\n\n".join(
        [
            f"TOPIC\n{draft.topic}",
            f"WORKING TITLE\n{draft.working_title}",
            f"CORE QUESTION\n{draft.core_question}",
            f"VIEWER PROMISE\n{draft.viewer_promise}",
            f"TARGET AUDIENCE\n{draft.target_audience}",
            f"CORE TAKEAWAY\n{draft.core_takeaway}",
            f"CONTENT ANGLE\n{draft.content_angle}",
            f"KEY FACTS\n{bullets(draft.key_facts)}",
            f"CLAIMS REQUIRING VERIFICATION\n{bullets(draft.claims_requiring_verification)}",
            f"SOURCE NOTES\n{bullets(draft.source_notes)}",
            f"EMOTIONAL DIRECTION\n{draft.emotional_direction}",
            f"VISUAL OPPORTUNITIES\n{bullets(draft.visual_opportunities)}",
            f"RISKS AND CAUTIONS\n{bullets(draft.risks_and_cautions)}",
            f"RECOMMENDED DURATION\n{draft.recommended_duration_seconds} seconds",
        ]
    )


# --- Story Spine -------------------------------------------------------------


class StoryBeat(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beat: int = Field(ge=1)
    purpose: str = ""
    content: str = ""
    estimated_seconds: int = Field(ge=1)

    @field_validator("purpose", "content")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()


class StorySpineDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: str = ""
    setup: str = ""
    curiosity_gap: str = ""
    progression: list[StoryBeat] = Field(default_factory=list)
    core_explanation: str = ""
    reveal_or_reframe: str = ""
    ending: str = ""
    call_to_action: str = ""
    visual_rhythm_notes: list[str] = Field(default_factory=list)
    retention_risks: list[str] = Field(default_factory=list)
    claims_requiring_verification: list[str] = Field(default_factory=list)
    estimated_total_seconds: int = Field(default=60, ge=1)

    @field_validator(
        "hook",
        "setup",
        "curiosity_gap",
        "core_explanation",
        "reveal_or_reframe",
        "ending",
        "call_to_action",
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator(
        "visual_rhythm_notes",
        "retention_risks",
        "claims_requiring_verification",
    )
    @classmethod
    def strip_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if str(item).strip()]


def story_spine_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "hook": {"type": "string"},
            "setup": {"type": "string"},
            "curiosity_gap": {"type": "string"},
            "progression": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "beat": {"type": "integer"},
                        "purpose": {"type": "string"},
                        "content": {"type": "string"},
                        "estimated_seconds": {"type": "integer"},
                    },
                    "required": ["beat", "purpose", "content", "estimated_seconds"],
                },
            },
            "core_explanation": {"type": "string"},
            "reveal_or_reframe": {"type": "string"},
            "ending": {"type": "string"},
            "call_to_action": {"type": "string"},
            "visual_rhythm_notes": {"type": "array", "items": {"type": "string"}},
            "retention_risks": {"type": "array", "items": {"type": "string"}},
            "claims_requiring_verification": {
                "type": "array",
                "items": {"type": "string"},
            },
            "estimated_total_seconds": {"type": "integer"},
        },
        "required": [
            "hook",
            "setup",
            "curiosity_gap",
            "progression",
            "core_explanation",
            "reveal_or_reframe",
            "ending",
            "call_to_action",
            "visual_rhythm_notes",
            "retention_risks",
            "claims_requiring_verification",
            "estimated_total_seconds",
        ],
    }


def parse_story_spine(payload: Any) -> StorySpineDraft:
    if isinstance(payload, str):
        payload = json.loads(payload)
    draft = StorySpineDraft.model_validate(payload)
    beats = sorted(draft.progression, key=lambda b: b.beat)
    expected = list(range(1, len(beats) + 1))
    actual = [b.beat for b in beats]
    if actual != expected:
        raise ValueError("Story spine beats must be consecutive starting at 1.")
    for beat in beats:
        if beat.estimated_seconds < 1:
            raise ValueError("Beat durations must be positive.")
    # Reassign sorted progression
    draft.progression = beats
    return draft


def story_spine_to_plain_text(draft: StorySpineDraft) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) if items else "- (none)"

    beat_lines = []
    for beat in draft.progression:
        beat_lines.append(
            f"{beat.beat}. [{beat.purpose}] ({beat.estimated_seconds}s)\n{beat.content}"
        )
    beats_block = "\n\n".join(beat_lines) if beat_lines else "(none)"
    return "\n\n".join(
        [
            f"HOOK\n{draft.hook}",
            f"SETUP\n{draft.setup}",
            f"CURIOSITY GAP\n{draft.curiosity_gap}",
            f"STORY BEATS\n{beats_block}",
            f"CORE EXPLANATION\n{draft.core_explanation}",
            f"REVEAL / REFRAME\n{draft.reveal_or_reframe}",
            f"ENDING\n{draft.ending}",
            f"CALL TO ACTION\n{draft.call_to_action}",
            f"VISUAL RHYTHM NOTES\n{bullets(draft.visual_rhythm_notes)}",
            f"RETENTION RISKS\n{bullets(draft.retention_risks)}",
            f"CLAIMS REQUIRING VERIFICATION\n{bullets(draft.claims_requiring_verification)}",
            f"ESTIMATED DURATION\n{draft.estimated_total_seconds} seconds",
        ]
    )


# --- Master Script -----------------------------------------------------------


class MasterScriptQualityChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    single_core_idea: bool = True
    clear_hook: bool = True
    clear_payoff: bool = True
    duration_target_met: bool = True


class MasterScriptDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    narration: str = ""
    hook: str = ""
    ending: str = ""
    estimated_word_count: int = Field(default=0, ge=0)
    estimated_duration_seconds: int = Field(default=60, ge=1)
    on_screen_keywords: list[str] = Field(default_factory=list)
    claims_requiring_verification: list[str] = Field(default_factory=list)
    editor_notes: list[str] = Field(default_factory=list)
    quality_checks: MasterScriptQualityChecks = Field(
        default_factory=MasterScriptQualityChecks
    )

    @field_validator("title", "narration", "hook", "ending")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator(
        "on_screen_keywords",
        "claims_requiring_verification",
        "editor_notes",
    )
    @classmethod
    def strip_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if str(item).strip()]


def master_script_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "narration": {"type": "string"},
            "hook": {"type": "string"},
            "ending": {"type": "string"},
            "estimated_word_count": {"type": "integer"},
            "estimated_duration_seconds": {"type": "integer"},
            "on_screen_keywords": {"type": "array", "items": {"type": "string"}},
            "claims_requiring_verification": {
                "type": "array",
                "items": {"type": "string"},
            },
            "editor_notes": {"type": "array", "items": {"type": "string"}},
            "quality_checks": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "single_core_idea": {"type": "boolean"},
                    "clear_hook": {"type": "boolean"},
                    "clear_payoff": {"type": "boolean"},
                    "duration_target_met": {"type": "boolean"},
                },
                "required": [
                    "single_core_idea",
                    "clear_hook",
                    "clear_payoff",
                    "duration_target_met",
                ],
            },
        },
        "required": [
            "title",
            "narration",
            "hook",
            "ending",
            "estimated_word_count",
            "estimated_duration_seconds",
            "on_screen_keywords",
            "claims_requiring_verification",
            "editor_notes",
            "quality_checks",
        ],
    }


def parse_master_script(payload: Any) -> MasterScriptDraft:
    if isinstance(payload, str):
        payload = json.loads(payload)
    return MasterScriptDraft.model_validate(payload)


def master_script_to_plain_text(draft: MasterScriptDraft) -> str:
    """Apply narration only to the Master Script document body."""
    return draft.narration.strip()


def schema_and_parser_for_purpose(purpose: str):
    if purpose == PURPOSE_DISCOVERY_BRIEF:
        return discovery_brief_json_schema(), parse_discovery_brief, "discovery_brief_draft"
    if purpose == PURPOSE_STORY_SPINE:
        return story_spine_json_schema(), parse_story_spine, "story_spine_draft"
    if purpose == PURPOSE_MASTER_SCRIPT:
        return master_script_json_schema(), parse_master_script, "master_script_draft"
    raise ValueError(f"Unknown script draft purpose: {purpose}")


def structured_to_plain_text(purpose: str, structured: dict[str, Any]) -> str:
    if purpose == PURPOSE_DISCOVERY_BRIEF:
        return discovery_brief_to_plain_text(parse_discovery_brief(structured))
    if purpose == PURPOSE_STORY_SPINE:
        return story_spine_to_plain_text(parse_story_spine(structured))
    if purpose == PURPOSE_MASTER_SCRIPT:
        return master_script_to_plain_text(parse_master_script(structured))
    raise ValueError(f"Unknown script draft purpose: {purpose}")
