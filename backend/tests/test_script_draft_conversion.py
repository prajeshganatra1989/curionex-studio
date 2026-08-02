"""Unit tests for script draft conversion, fingerprints, and word-count helpers."""

from __future__ import annotations

import pytest

from app.ai.script_draft import (
    DOCUMENT_TYPE_BY_PURPOSE,
    PURPOSE_BY_DOCUMENT_TYPE,
    PURPOSE_DISCOVERY_BRIEF,
    PURPOSE_MASTER_SCRIPT,
    PURPOSE_STORY_SPINE,
    SCRIPT_DRAFT_PURPOSES,
    DiscoveryBriefDraft,
    MasterScriptDraft,
    StorySpineDraft,
    content_fingerprint,
    discovery_brief_to_plain_text,
    master_script_to_plain_text,
    parse_discovery_brief,
    parse_master_script,
    parse_story_spine,
    story_spine_to_plain_text,
    target_word_range,
    word_count,
)

SAMPLE_DISCOVERY = {
    "topic": "Black holes",
    "working_title": "Edge of Darkness",
    "core_question": "What happens at the event horizon?",
    "viewer_promise": "A clear mental model of black holes",
    "target_audience": "Curious adults",
    "core_takeaway": "Gravity warps spacetime",
    "content_angle": "Accessible astrophysics",
    "key_facts": ["Event horizons exist", "Hawking radiation is theoretical"],
    "claims_requiring_verification": ["Exact horizon behavior"],
    "source_notes": ["NASA overview"],
    "emotional_direction": "Wonder without fear",
    "visual_opportunities": ["Spacetime grid warp"],
    "risks_and_cautions": ["Avoid sensational claims"],
    "recommended_duration_seconds": 60,
}

SAMPLE_SPINE = {
    "hook": "Space can trap light.",
    "setup": "A star collapses.",
    "curiosity_gap": "Where does the matter go?",
    "progression": [
        {
            "beat": 2,
            "purpose": "escalate",
            "content": "Escape velocity exceeds light.",
            "estimated_seconds": 10,
        },
        {
            "beat": 1,
            "purpose": "establish",
            "content": "Mass curves spacetime.",
            "estimated_seconds": 8,
        },
    ],
    "core_explanation": "The horizon is a boundary in spacetime.",
    "reveal_or_reframe": "Nothing dramatic happens locally.",
    "ending": "Gravity is geometry.",
    "call_to_action": "Explore more cosmology shorts.",
    "visual_rhythm_notes": ["Slow push-in"],
    "retention_risks": ["Jargon overload"],
    "claims_requiring_verification": ["Exact collapse dynamics"],
    "estimated_total_seconds": 60,
}

SAMPLE_MASTER = {
    "title": "Edge of Darkness",
    "narration": "Light can vanish into a black hole.",
    "hook": "Space can trap light.",
    "ending": "Gravity is geometry.",
    "estimated_word_count": 7,
    "estimated_duration_seconds": 60,
    "on_screen_keywords": ["horizon", "spacetime"],
    "claims_requiring_verification": ["Exact horizon behavior"],
    "editor_notes": ["Keep spoken cadence"],
    "quality_checks": {
        "single_core_idea": True,
        "clear_hook": True,
        "clear_payoff": True,
        "duration_target_met": True,
    },
}


def test_purpose_codes_unique_and_mapped() -> None:
    assert len(SCRIPT_DRAFT_PURPOSES) == 3
    assert PURPOSE_DISCOVERY_BRIEF != PURPOSE_STORY_SPINE != PURPOSE_MASTER_SCRIPT
    assert PURPOSE_DISCOVERY_BRIEF != PURPOSE_MASTER_SCRIPT
    assert set(DOCUMENT_TYPE_BY_PURPOSE.values()) == {
        "discovery_brief",
        "story_spine",
        "master_script",
    }
    assert PURPOSE_BY_DOCUMENT_TYPE["discovery_brief"] == PURPOSE_DISCOVERY_BRIEF
    assert PURPOSE_BY_DOCUMENT_TYPE["story_spine"] == PURPOSE_STORY_SPINE
    assert PURPOSE_BY_DOCUMENT_TYPE["master_script"] == PURPOSE_MASTER_SCRIPT


def test_content_fingerprint_normalized() -> None:
    assert content_fingerprint("  hello  ") == content_fingerprint("hello")
    assert content_fingerprint("a") != content_fingerprint("b")
    assert content_fingerprint("") == content_fingerprint("   ")
    assert len(content_fingerprint("x")) == 64


def test_word_count() -> None:
    assert word_count("") == 0
    assert word_count("one two three") == 3
    assert word_count("It's a test — really.") == 4
    assert word_count("alpha " * 10) == 10


def test_target_word_range_default_tolerance() -> None:
    lo, target, hi = target_word_range(
        target_duration_seconds=60,
        target_words_per_minute=150,
    )
    assert target == 150
    assert lo == 135
    assert hi == 165

    lo2, target2, hi2 = target_word_range(
        target_duration_seconds=90,
        target_words_per_minute=120,
        tolerance=0.0,
    )
    assert lo2 == target2 == hi2 == 180


def test_discovery_brief_to_plain_text_deterministic() -> None:
    draft = parse_discovery_brief(SAMPLE_DISCOVERY)
    assert isinstance(draft, DiscoveryBriefDraft)
    text = discovery_brief_to_plain_text(draft)
    again = discovery_brief_to_plain_text(parse_discovery_brief(SAMPLE_DISCOVERY))
    assert text == again
    assert text.startswith("TOPIC\nBlack holes")
    assert "KEY FACTS\n- Event horizons exist" in text
    assert "RECOMMENDED DURATION\n60 seconds" in text


def test_story_spine_sorts_beats_and_converts() -> None:
    draft = parse_story_spine(SAMPLE_SPINE)
    assert isinstance(draft, StorySpineDraft)
    assert [b.beat for b in draft.progression] == [1, 2]
    text = story_spine_to_plain_text(draft)
    assert "1. [establish] (8s)" in text
    assert "2. [escalate] (10s)" in text
    assert text == story_spine_to_plain_text(parse_story_spine(SAMPLE_SPINE))


def test_story_spine_rejects_nonconsecutive_beats() -> None:
    bad = dict(SAMPLE_SPINE)
    bad["progression"] = [
        {
            "beat": 1,
            "purpose": "a",
            "content": "x",
            "estimated_seconds": 5,
        },
        {
            "beat": 3,
            "purpose": "b",
            "content": "y",
            "estimated_seconds": 5,
        },
    ]
    with pytest.raises(ValueError, match="consecutive"):
        parse_story_spine(bad)


def test_master_script_to_plain_text_narration_only() -> None:
    draft = parse_master_script(SAMPLE_MASTER)
    assert isinstance(draft, MasterScriptDraft)
    text = master_script_to_plain_text(draft)
    assert text == "Light can vanish into a black hole."
    assert "Edge of Darkness" not in text
    assert "horizon" not in text or text == draft.narration
