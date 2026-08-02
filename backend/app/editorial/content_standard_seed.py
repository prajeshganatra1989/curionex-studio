"""Seed payload for Curionex Content Standard v1."""

from app.editorial.content_standard_constants import (
    CONTENT_STANDARD_STATUS_ACTIVE,
    DEFAULT_CONTENT_STANDARD_NAME,
    DEFAULT_CONTENT_STANDARD_VERSION,
)

CONTENT_STANDARD_V1: dict = {
    "name": DEFAULT_CONTENT_STANDARD_NAME,
    "version": DEFAULT_CONTENT_STANDARD_VERSION,
    "status": CONTENT_STANDARD_STATUS_ACTIVE,
    "mission": ("Explain fascinating topics with clarity, curiosity and credibility."),
    "target_audience": ("General audience, 13+, English-speaking curious learners."),
    "brand_voice": ("Friendly, confident, conversational, curious, and trustworthy."),
    "editorial_principles": (
        "- One memorable idea\n"
        "- Clear explanation\n"
        "- High retention\n"
        "- No fluff\n"
        "- Respect viewer intelligence"
    ),
    "hook_rules": (
        "- Create curiosity immediately\n"
        "- Never use misleading clickbait\n"
        "- Viewer should understand the promise within 5 seconds"
    ),
    "story_structure": ("Hook → Context → Explanation → Twist → Payoff → CTA"),
    "fact_policy": (
        "- Never invent statistics\n"
        "- Never invent quotes\n"
        "- State uncertainty honestly\n"
        "- Distinguish theory from evidence"
    ),
    "citation_policy": ("- Prefer authoritative sources\n- Avoid unsupported claims"),
    "tone_guidelines": (
        "- Natural spoken English\n"
        "- Short sentences\n"
        "- No robotic wording\n"
        "- No academic jargon"
    ),
    "language_rules": (
        "- Prefer concrete verbs and everyday vocabulary\n"
        "- Keep one idea per sentence when possible\n"
        "- Write for the ear, not the page"
    ),
    "forbidden_patterns": (
        "- Overhype\n"
        "- Fear bait\n"
        "- Conspiracy framing\n"
        "- False certainty\n"
        "- Clickbait promises"
    ),
    "approved_cta_patterns": (
        "- Follow for more fascinating facts.\n- Comment your favourite fact."
    ),
    "quality_checklist": (
        "- Curiosity\n"
        "- Clarity\n"
        "- Accuracy\n"
        "- Retention\n"
        "- Natural narration\n"
        "- Viewer payoff"
    ),
    "default_duration_seconds": 60,
    "default_target_words": 160,
    "notes": "Seeded Curionex Content Standard v1 — single editorial source of truth.",
}
