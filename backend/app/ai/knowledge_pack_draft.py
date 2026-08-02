"""Knowledge Pack draft structured schema and plain-text conversion."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.knowledge_packs.catalog import SECTION_KEYS

PURPOSE_KNOWLEDGE_PACK_DRAFT = "knowledge_pack.draft"

APPLYABLE_SECTIONS: frozenset[str] = frozenset(
    {
        "research",
        "facts",
        "sources",
        "audience",
        "content_angle",
        "key_insights",
        "additional_context",
    }
)

ConflictStrategy = Literal[
    "reject_if_non_empty",
    "replace_selected",
    "append_selected",
]

DEFAULT_CONFLICT_STRATEGY: ConflictStrategy = "reject_if_non_empty"


class DraftSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    verification_status: Literal["unverified"] = "unverified"

    @field_validator("label", "reference")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("verification_status", mode="before")
    @classmethod
    def force_unverified(cls, value: Any) -> str:
        # Model must never claim verified sources.
        return "unverified"


class KnowledgePackDraft(BaseModel):
    """Strict structured draft returned by the OpenAI Responses API."""

    model_config = ConfigDict(extra="forbid")

    research: str = ""
    facts: list[str] = Field(default_factory=list)
    sources: list[DraftSource] = Field(default_factory=list)
    audience: str = ""
    content_angle: str = ""
    key_insights: list[str] = Field(default_factory=list)
    additional_context: str = ""
    warnings: list[str] = Field(default_factory=list)

    @field_validator("research", "audience", "content_angle", "additional_context")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator("facts", "key_insights", "warnings")
    @classmethod
    def strip_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if str(item).strip()]


def knowledge_pack_draft_json_schema() -> dict[str, Any]:
    """JSON Schema for Responses API text.format (strict)."""
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "research": {"type": "string"},
            "facts": {"type": "array", "items": {"type": "string"}},
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "label": {"type": "string"},
                        "reference": {"type": "string"},
                        "verification_status": {
                            "type": "string",
                            "enum": ["unverified"],
                        },
                    },
                    "required": ["label", "reference", "verification_status"],
                },
            },
            "audience": {"type": "string"},
            "content_angle": {"type": "string"},
            "key_insights": {"type": "array", "items": {"type": "string"}},
            "additional_context": {"type": "string"},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "research",
            "facts",
            "sources",
            "audience",
            "content_angle",
            "key_insights",
            "additional_context",
            "warnings",
        ],
    }


def parse_knowledge_pack_draft(payload: Any) -> KnowledgePackDraft:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Output is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Output must be a JSON object.")
    return KnowledgePackDraft.model_validate(payload)


def draft_section_to_plain_text(section_key: str, draft: KnowledgePackDraft) -> str:
    """Convert one structured field into plain-text Knowledge Pack content."""
    if section_key not in APPLYABLE_SECTIONS:
        raise ValueError(f"Invalid section key: {section_key}")
    if section_key not in SECTION_KEYS:
        raise ValueError(f"Unknown Knowledge Pack section: {section_key}")

    if section_key == "research":
        return draft.research.strip()
    if section_key == "audience":
        return draft.audience.strip()
    if section_key == "content_angle":
        return draft.content_angle.strip()
    if section_key == "additional_context":
        return draft.additional_context.strip()
    if section_key == "facts":
        return "\n".join(f"- {item}" for item in draft.facts)
    if section_key == "key_insights":
        return "\n".join(f"- {item}" for item in draft.key_insights)
    if section_key == "sources":
        lines: list[str] = []
        for source in draft.sources:
            lines.append(
                f"- {source.label}: {source.reference} "
                "[UNVERIFIED — HUMAN CHECK REQUIRED]"
            )
        return "\n".join(lines)
    raise ValueError(f"Unhandled section key: {section_key}")


def draft_to_section_map(draft: KnowledgePackDraft) -> dict[str, str]:
    return {
        key: draft_section_to_plain_text(key, draft)
        for key in sorted(APPLYABLE_SECTIONS)
    }
