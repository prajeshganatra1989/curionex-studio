"""Script AI quality review — purpose, schema, scoring policy, and enrichment."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.ai.script_draft import (
    DEFAULT_TARGET_DURATION_SECONDS,
    DEFAULT_TARGET_WORDS_PER_MINUTE,
    DURATION_WORD_COUNT_TOLERANCE,
    content_fingerprint,
    target_word_range,
    word_count,
)

PURPOSE_QUALITY_REVIEW = "script.quality_review"

QUALITY_REVIEW_PURPOSES: frozenset[str] = frozenset({PURPOSE_QUALITY_REVIEW})

# Target document for association / idempotency sentinel.
QUALITY_REVIEW_DOCUMENT_TYPE = "master_script"

REVIEW_DIMENSIONS: tuple[str, ...] = (
    "hook",
    "curiosity",
    "retention",
    "clarity",
    "structure",
    "factual_safety",
    "viewer_promise",
    "payoff",
    "pacing",
    "spoken_naturalness",
    "conciseness",
    "brand_voice",
    "call_to_action",
    "duration_fit",
)

# Weights must total 100.
DIMENSION_WEIGHTS: dict[str, int] = {
    "hook": 10,
    "curiosity": 8,
    "retention": 12,
    "clarity": 10,
    "structure": 8,
    "factual_safety": 12,
    "viewer_promise": 8,
    "payoff": 8,
    "pacing": 7,
    "spoken_naturalness": 6,
    "conciseness": 4,
    "brand_voice": 3,
    "call_to_action": 2,
    "duration_fit": 2,
}

assert sum(DIMENSION_WEIGHTS.values()) == 100
assert set(DIMENSION_WEIGHTS) == set(REVIEW_DIMENSIONS)

MAX_PRIORITY_ISSUES = 10
MAX_EXCERPT_CHARS = 400
MAX_REWRITE_CHARS = 800
HUMAN_REVIEW_SCORE_THRESHOLD = 80
READY_FOR_VERSION_SCORE_THRESHOLD = 90

QualityBand = Literal[
    "excellent",
    "strong",
    "needs_refinement",
    "weak",
    "major_revision_required",
]
Recommendation = Literal["revise", "human_review", "ready_for_version"]
Severity = Literal["critical", "high", "medium", "low"]
RiskLevel = Literal["high", "medium", "low"]
Confidence = Literal["high", "medium", "low"]
PacingStatus = Literal["short", "within_range", "long"]
SuggestionStrategy = Literal["replace_excerpt"]

ISSUE_CATEGORIES: frozenset[str] = frozenset(
    {
        "hook",
        "fact",
        "retention",
        "clarity",
        "pacing",
        "structure",
        "payoff",
        "language",
        "cta",
        "brand_voice",
    }
)

QUALITY_BAND_LABELS: dict[QualityBand, str] = {
    "excellent": "Excellent",
    "strong": "Strong",
    "needs_refinement": "Needs Refinement",
    "weak": "Weak",
    "major_revision_required": "Major Revision Required",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class DimensionReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    assessment: str = ""
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    suggested_action: str = ""

    @field_validator("assessment", "suggested_action")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator("strengths", "issues")
    @classmethod
    def clean_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in (value or []) if item and str(item).strip()]


class PriorityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    severity: Severity
    category: str
    location_hint: str = ""
    original_excerpt: str = ""
    problem: str = ""
    recommended_change: str = ""
    suggested_rewrite: str | None = None

    @field_validator("id", "location_hint", "problem", "recommended_change")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return (value or "").strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if cleaned not in ISSUE_CATEGORIES:
            raise ValueError(f"Invalid issue category: {cleaned!r}")
        return cleaned

    @field_validator("original_excerpt")
    @classmethod
    def limit_excerpt(cls, value: str) -> str:
        text = (value or "").strip()
        return text[:MAX_EXCERPT_CHARS]

    @field_validator("suggested_rewrite")
    @classmethod
    def limit_rewrite(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        return text[:MAX_REWRITE_CHARS]


class FactualRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str
    risk_level: RiskLevel
    reason: str = ""
    verification_needed: bool = True
    related_source_note: str | None = None

    @field_validator("claim", "reason")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return (value or "").strip()

    @model_validator(mode="after")
    def force_verification(self) -> FactualRisk:
        self.verification_needed = True
        return self


class RepeatedLanguage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str
    count: int = Field(ge=1)
    suggestions: list[str] = Field(default_factory=list)

    @field_validator("term")
    @classmethod
    def strip_term(cls, value: str) -> str:
        return (value or "").strip()


class PacingAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_word_count: int = Field(ge=0)
    estimated_duration_seconds: int = Field(ge=0)
    target_duration_seconds: int = Field(ge=1)
    status: PacingStatus
    slow_sections: list[str] = Field(default_factory=list)
    rushed_sections: list[str] = Field(default_factory=list)


class PromiseAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    promise_made: str = ""
    promise_delivered: bool = False
    explanation: str = ""


class ScriptQualityReview(BaseModel):
    """Model-facing review schema (before server enrichment)."""

    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    confidence: Confidence = "medium"
    summary: str = ""
    ready_for_human_review: bool = False
    dimensions: dict[str, DimensionReview]
    priority_issues: list[PriorityIssue] = Field(default_factory=list)
    factual_risks: list[FactualRisk] = Field(default_factory=list)
    repeated_language: list[RepeatedLanguage] = Field(default_factory=list)
    pacing_analysis: PacingAnalysis
    promise_analysis: PromiseAnalysis
    recommended_next_action: Recommendation = "human_review"
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dimensions(self) -> ScriptQualityReview:
        missing = [key for key in REVIEW_DIMENSIONS if key not in self.dimensions]
        if missing:
            raise ValueError(f"Missing review dimensions: {', '.join(missing)}")
        extra = [key for key in self.dimensions if key not in REVIEW_DIMENSIONS]
        if extra:
            raise ValueError(f"Unsupported review dimensions: {', '.join(extra)}")
        if len(self.priority_issues) > MAX_PRIORITY_ISSUES:
            self.priority_issues = self.priority_issues[:MAX_PRIORITY_ISSUES]
        return self


def quality_review_json_schema() -> dict[str, Any]:
    dimension_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "score",
            "assessment",
            "strengths",
            "issues",
            "suggested_action",
        ],
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "assessment": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "issues": {"type": "array", "items": {"type": "string"}},
            "suggested_action": {"type": "string"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "overall_score",
            "confidence",
            "summary",
            "ready_for_human_review",
            "dimensions",
            "priority_issues",
            "factual_risks",
            "repeated_language",
            "pacing_analysis",
            "promise_analysis",
            "recommended_next_action",
            "warnings",
        ],
        "properties": {
            "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
            "summary": {"type": "string"},
            "ready_for_human_review": {"type": "boolean"},
            "dimensions": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REVIEW_DIMENSIONS),
                "properties": {key: dimension_schema for key in REVIEW_DIMENSIONS},
            },
            "priority_issues": {
                "type": "array",
                "maxItems": MAX_PRIORITY_ISSUES,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "id",
                        "severity",
                        "category",
                        "location_hint",
                        "original_excerpt",
                        "problem",
                        "recommended_change",
                        "suggested_rewrite",
                    ],
                    "properties": {
                        "id": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"],
                        },
                        "category": {
                            "type": "string",
                            "enum": sorted(ISSUE_CATEGORIES),
                        },
                        "location_hint": {"type": "string"},
                        "original_excerpt": {"type": "string"},
                        "problem": {"type": "string"},
                        "recommended_change": {"type": "string"},
                        "suggested_rewrite": {
                            "type": ["string", "null"],
                        },
                    },
                },
            },
            "factual_risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "claim",
                        "risk_level",
                        "reason",
                        "verification_needed",
                        "related_source_note",
                    ],
                    "properties": {
                        "claim": {"type": "string"},
                        "risk_level": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "reason": {"type": "string"},
                        "verification_needed": {"type": "boolean"},
                        "related_source_note": {"type": ["string", "null"]},
                    },
                },
            },
            "repeated_language": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["term", "count", "suggestions"],
                    "properties": {
                        "term": {"type": "string"},
                        "count": {"type": "integer", "minimum": 1},
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
            },
            "pacing_analysis": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "estimated_word_count",
                    "estimated_duration_seconds",
                    "target_duration_seconds",
                    "status",
                    "slow_sections",
                    "rushed_sections",
                ],
                "properties": {
                    "estimated_word_count": {"type": "integer", "minimum": 0},
                    "estimated_duration_seconds": {"type": "integer", "minimum": 0},
                    "target_duration_seconds": {"type": "integer", "minimum": 1},
                    "status": {
                        "type": "string",
                        "enum": ["short", "within_range", "long"],
                    },
                    "slow_sections": {"type": "array", "items": {"type": "string"}},
                    "rushed_sections": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            "promise_analysis": {
                "type": "object",
                "additionalProperties": False,
                "required": ["promise_made", "promise_delivered", "explanation"],
                "properties": {
                    "promise_made": {"type": "string"},
                    "promise_delivered": {"type": "boolean"},
                    "explanation": {"type": "string"},
                },
            },
            "recommended_next_action": {
                "type": "string",
                "enum": ["revise", "human_review", "ready_for_version"],
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


def parse_quality_review(payload: Any) -> ScriptQualityReview:
    if isinstance(payload, str):
        payload = json.loads(payload)
    return ScriptQualityReview.model_validate(payload)


def calculate_weighted_score(dimensions: dict[str, DimensionReview]) -> int:
    total = 0.0
    for key, weight in DIMENSION_WEIGHTS.items():
        total += dimensions[key].score * (weight / 100.0)
    return int(round(total))


def quality_band_for_score(score: int) -> QualityBand:
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "strong"
    if score >= 70:
        return "needs_refinement"
    if score >= 60:
        return "weak"
    return "major_revision_required"


def pacing_status_for(
    *,
    word_count_value: int,
    target_duration_seconds: int,
    target_words_per_minute: int,
) -> PacingStatus:
    lo, _target, hi = target_word_range(
        target_duration_seconds=target_duration_seconds,
        target_words_per_minute=target_words_per_minute,
        tolerance=DURATION_WORD_COUNT_TOLERANCE,
    )
    if word_count_value < lo:
        return "short"
    if word_count_value > hi:
        return "long"
    return "within_range"


def estimated_duration_seconds(
    *,
    word_count_value: int,
    target_words_per_minute: int,
) -> int:
    wpm = max(1, target_words_per_minute)
    return max(1, int(round((word_count_value / wpm) * 60)))


def recommend_next_action(
    *,
    overall_score: int,
    factual_risks: list[FactualRisk],
    priority_issues: list[PriorityIssue],
) -> Recommendation:
    has_critical_fact = any(risk.risk_level == "high" for risk in factual_risks)
    has_critical_issue = any(issue.severity == "critical" for issue in priority_issues)
    if has_critical_fact or has_critical_issue:
        return "revise"
    if overall_score < HUMAN_REVIEW_SCORE_THRESHOLD:
        return "revise"
    if (
        overall_score >= READY_FOR_VERSION_SCORE_THRESHOLD
        and not any(risk.risk_level in {"high", "medium"} for risk in factual_risks)
        and not any(issue.severity in {"critical", "high"} for issue in priority_issues)
    ):
        return "ready_for_version"
    return "human_review"


def sort_priority_issues(issues: list[PriorityIssue]) -> list[PriorityIssue]:
    return sorted(
        issues,
        key=lambda issue: (SEVERITY_ORDER.get(issue.severity, 99), issue.id),
    )


def enrich_quality_review(
    review: ScriptQualityReview,
    *,
    master_script: str,
    target_duration_seconds: int = DEFAULT_TARGET_DURATION_SECONDS,
    target_words_per_minute: int = DEFAULT_TARGET_WORDS_PER_MINUTE,
    context_warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Apply server-side scoring, metrics, and recommendation policy."""
    model_overall_score = review.overall_score
    calculated = calculate_weighted_score(review.dimensions)
    words = word_count(master_script)
    duration = estimated_duration_seconds(
        word_count_value=words,
        target_words_per_minute=target_words_per_minute,
    )
    status = pacing_status_for(
        word_count_value=words,
        target_duration_seconds=target_duration_seconds,
        target_words_per_minute=target_words_per_minute,
    )

    issues = sort_priority_issues(review.priority_issues)[:MAX_PRIORITY_ISSUES]
    risks = list(review.factual_risks)
    for risk in risks:
        risk.verification_needed = True

    recommendation = recommend_next_action(
        overall_score=calculated,
        factual_risks=risks,
        priority_issues=issues,
    )
    band = quality_band_for_score(calculated)
    warnings = list(review.warnings)
    for item in context_warnings or []:
        if item and item not in warnings:
            warnings.append(item)
    if model_overall_score != calculated:
        warnings.append(
            "Displayed overall score is server-calculated from weighted dimensions; "
            f"model-provided overall score was {model_overall_score}."
        )

    payload = review.model_dump()
    payload["model_overall_score"] = model_overall_score
    payload["overall_score"] = calculated
    payload["calculated_overall_score"] = calculated
    payload["quality_band"] = band
    payload["quality_band_label"] = QUALITY_BAND_LABELS[band]
    payload["recommended_next_action"] = recommendation
    # AI never approves content.
    payload["ready_for_human_review"] = recommendation in {
        "human_review",
        "ready_for_version",
    }
    payload["priority_issues"] = [issue.model_dump() for issue in issues]
    payload["factual_risks"] = [risk.model_dump() for risk in risks]
    payload["pacing_analysis"] = {
        "estimated_word_count": words,
        "estimated_duration_seconds": duration,
        "target_duration_seconds": target_duration_seconds,
        "target_words_per_minute": target_words_per_minute,
        "status": status,
        "slow_sections": list(review.pacing_analysis.slow_sections),
        "rushed_sections": list(review.pacing_analysis.rushed_sections),
        "source": "server_metrics_plus_ai_sections",
    }
    payload["deterministic_metrics"] = {
        "word_count": words,
        "estimated_duration_seconds": duration,
        "target_duration_seconds": target_duration_seconds,
        "target_words_per_minute": target_words_per_minute,
        "pacing_status": status,
        "master_script_fingerprint": content_fingerprint(master_script),
    }
    payload["score_weights"] = dict(DIMENSION_WEIGHTS)
    payload["warnings"] = warnings
    payload["ai_approval"] = False
    return payload


def policy_fingerprint() -> str:
    blob = json.dumps(
        {
            "weights": DIMENSION_WEIGHTS,
            "max_issues": MAX_PRIORITY_ISSUES,
            "human_review_threshold": HUMAN_REVIEW_SCORE_THRESHOLD,
            "ready_threshold": READY_FOR_VERSION_SCORE_THRESHOLD,
            "tolerance": DURATION_WORD_COUNT_TOLERANCE,
        },
        sort_keys=True,
    )
    return content_fingerprint(blob)
