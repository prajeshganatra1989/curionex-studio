"""Pure unit tests for script quality scoring policy — no DB / API."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.ai.script_draft import word_count
from app.ai.script_quality_review import (
    DIMENSION_WEIGHTS,
    REVIEW_DIMENSIONS,
    DimensionReview,
    FactualRisk,
    PacingAnalysis,
    PriorityIssue,
    PromiseAnalysis,
    ScriptQualityReview,
    calculate_weighted_score,
    enrich_quality_review,
    parse_quality_review,
    quality_band_for_score,
    recommend_next_action,
)


def _dim(score: int) -> DimensionReview:
    return DimensionReview(
        score=score,
        assessment="ok",
        strengths=["clear"],
        issues=[],
        suggested_action="none",
    )


def _dimensions(score: int = 80) -> dict[str, DimensionReview]:
    return {key: _dim(score) for key in REVIEW_DIMENSIONS}


def _dimensions_scores(scores: dict[str, int]) -> dict[str, DimensionReview]:
    base = {key: 0 for key in REVIEW_DIMENSIONS}
    base.update(scores)
    return {key: _dim(value) for key, value in base.items()}


def _pacing() -> PacingAnalysis:
    return PacingAnalysis(
        estimated_word_count=120,
        estimated_duration_seconds=48,
        target_duration_seconds=60,
        status="within_range",
        slow_sections=[],
        rushed_sections=[],
    )


def _promise() -> PromiseAnalysis:
    return PromiseAnalysis(
        promise_made="Explain black holes clearly",
        promise_delivered=True,
        explanation="Core idea lands.",
    )


def _review(**overrides) -> ScriptQualityReview:
    payload = {
        "overall_score": 80,
        "confidence": "medium",
        "summary": "Solid short.",
        "ready_for_human_review": True,
        "dimensions": {key: _dim(80).model_dump() for key in REVIEW_DIMENSIONS},
        "priority_issues": [],
        "factual_risks": [],
        "repeated_language": [],
        "pacing_analysis": _pacing().model_dump(),
        "promise_analysis": _promise().model_dump(),
        "recommended_next_action": "human_review",
        "warnings": [],
    }
    payload.update(overrides)
    return parse_quality_review(payload)


def test_dimension_weights_sum_100() -> None:
    assert sum(DIMENSION_WEIGHTS.values()) == 100
    assert set(DIMENSION_WEIGHTS) == set(REVIEW_DIMENSIONS)


def test_calculate_weighted_score_uniform() -> None:
    assert calculate_weighted_score(_dimensions(80)) == 80
    assert calculate_weighted_score(_dimensions(100)) == 100
    assert calculate_weighted_score(_dimensions(0)) == 0


def test_calculate_weighted_score_weighted_mix() -> None:
    # retention (12) and factual_safety (12) at 100, everything else at 0
    dims = _dimensions_scores({"retention": 100, "factual_safety": 100})
    # 12 + 12 = 24
    assert calculate_weighted_score(dims) == 24

    dims2 = _dimensions_scores(
        {
            "hook": 100,  # 10
            "curiosity": 50,  # 4
            "retention": 0,
        }
    )
    assert calculate_weighted_score(dims2) == 14


def test_quality_band_for_score() -> None:
    assert quality_band_for_score(95) == "excellent"
    assert quality_band_for_score(90) == "excellent"
    assert quality_band_for_score(85) == "strong"
    assert quality_band_for_score(80) == "strong"
    assert quality_band_for_score(75) == "needs_refinement"
    assert quality_band_for_score(70) == "needs_refinement"
    assert quality_band_for_score(65) == "weak"
    assert quality_band_for_score(60) == "weak"
    assert quality_band_for_score(59) == "major_revision_required"
    assert quality_band_for_score(0) == "major_revision_required"


def test_recommend_next_action_critical_fact_forces_revise() -> None:
    risks = [
        FactualRisk(
            claim="Exact horizon temperature",
            risk_level="high",
            reason="Unverified number",
            verification_needed=True,
            related_source_note=None,
        )
    ]
    assert (
        recommend_next_action(
            overall_score=95,
            factual_risks=risks,
            priority_issues=[],
        )
        == "revise"
    )


def test_recommend_next_action_critical_issue_forces_revise() -> None:
    issues = [
        PriorityIssue(
            id="iss-1",
            severity="critical",
            category="hook",
            location_hint="opening",
            original_excerpt="Space can trap light.",
            problem="Weak hook",
            recommended_change="Sharpen opening",
            suggested_rewrite=None,
        )
    ]
    assert (
        recommend_next_action(
            overall_score=92,
            factual_risks=[],
            priority_issues=issues,
        )
        == "revise"
    )


def test_recommend_next_action_score_bands() -> None:
    assert (
        recommend_next_action(
            overall_score=79,
            factual_risks=[],
            priority_issues=[],
        )
        == "revise"
    )
    assert (
        recommend_next_action(
            overall_score=85,
            factual_risks=[],
            priority_issues=[],
        )
        == "human_review"
    )
    assert (
        recommend_next_action(
            overall_score=90,
            factual_risks=[],
            priority_issues=[],
        )
        == "ready_for_version"
    )


def test_recommend_next_action_medium_risk_blocks_ready() -> None:
    risks = [
        FactualRisk(
            claim="Hawking radiation details",
            risk_level="medium",
            reason="Needs source check",
            verification_needed=True,
            related_source_note="NASA overview",
        )
    ]
    assert (
        recommend_next_action(
            overall_score=95,
            factual_risks=risks,
            priority_issues=[],
        )
        == "human_review"
    )


def test_enrich_quality_review_stores_model_vs_calculated() -> None:
    narration = (
        "Space can trap light. When a massive star collapses, gravity warps spacetime "
        "so sharply that escape velocity exceeds the speed of light. That boundary is "
        "the event horizon — not a solid surface, but a one-way door in geometry. From "
        "far away, clocks near the horizon appear to freeze. Locally, nothing dramatic "
        "happens as you cross. Matter falls inward, and our everyday intuitions about "
        "space fail. Hawking radiation remains theoretical, so treat absolute claims "
        "with care. The takeaway is simple: gravity is geometry, and black holes are "
        "regions where that geometry closes off the outside universe. Stay curious, "
        "check the sources, and explore more cosmology shorts."
    )
    # Model claims 99; weighted dimensions all 70 → calculated 70
    review = _review(
        overall_score=99,
        dimensions={key: _dim(70).model_dump() for key in REVIEW_DIMENSIONS},
        recommended_next_action="ready_for_version",
        ready_for_human_review=True,
    )
    enriched = enrich_quality_review(
        review,
        master_script=narration,
        target_duration_seconds=60,
        target_words_per_minute=150,
        context_warnings=["Discovery Brief is empty."],
    )

    assert enriched["model_overall_score"] == 99
    assert enriched["overall_score"] == 70
    assert enriched["calculated_overall_score"] == 70
    assert enriched["quality_band"] == "needs_refinement"
    assert enriched["recommended_next_action"] == "revise"
    assert enriched["ai_approval"] is False
    assert enriched["ready_for_human_review"] is False
    assert enriched["deterministic_metrics"]["word_count"] == word_count(narration)
    assert enriched["deterministic_metrics"]["estimated_duration_seconds"] == max(
        1, int(round((word_count(narration) / 150) * 60))
    )
    assert "Discovery Brief is empty." in enriched["warnings"]
    assert any(
        "server-calculated" in w.lower() or "model-provided" in w.lower()
        for w in enriched["warnings"]
    )
    assert enriched["score_weights"] == dict(DIMENSION_WEIGHTS)
    # Factual risks always require verification
    assert all(r["verification_needed"] is True for r in enriched["factual_risks"])


def test_enrich_never_auto_approves() -> None:
    review = _review(
        overall_score=95,
        dimensions={key: _dim(95).model_dump() for key in REVIEW_DIMENSIONS},
        ready_for_human_review=True,
        recommended_next_action="ready_for_version",
    )
    enriched = enrich_quality_review(review, master_script="Short narration here.")
    assert enriched["ai_approval"] is False
    assert enriched["recommended_next_action"] == "ready_for_version"
    # ready_for_version still means human gate — not AI approval
    assert enriched["ready_for_human_review"] is True


def test_parse_quality_review_rejects_bad_schema() -> None:
    with pytest.raises((ValidationError, ValueError)):
        parse_quality_review({"overall_score": 80})

    bad_score = _review().model_dump()
    bad_score["dimensions"]["hook"]["score"] = 150
    with pytest.raises(ValidationError):
        parse_quality_review(bad_score)

    missing_dim = _review().model_dump()
    del missing_dim["dimensions"]["hook"]
    with pytest.raises(ValidationError):
        parse_quality_review(missing_dim)

    bad_category = _review().model_dump()
    bad_category["priority_issues"] = [
        {
            "id": "x",
            "severity": "high",
            "category": "not_a_real_category",
            "location_hint": "",
            "original_excerpt": "a",
            "problem": "p",
            "recommended_change": "c",
            "suggested_rewrite": None,
        }
    ]
    with pytest.raises(ValidationError):
        parse_quality_review(bad_category)


def test_parse_quality_review_accepts_valid_payload() -> None:
    review = _review()
    assert isinstance(review, ScriptQualityReview)
    assert set(review.dimensions) == set(REVIEW_DIMENSIONS)
