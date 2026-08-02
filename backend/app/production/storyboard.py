"""Deterministic storyboard / subtitle helpers for production packages."""

from __future__ import annotations

import re
from typing import Literal

ScenePurpose = Literal[
    "hook",
    "question",
    "explanation",
    "twist",
    "perspective_shift",
    "cta",
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)

# At 150 WPM: 3–6s ≈ 7.5–15 words
MIN_SCENE_WORDS = 8
MAX_SCENE_WORDS = 15
TARGET_SCENE_SECONDS_MIN = 3.0
TARGET_SCENE_SECONDS_MAX = 6.0


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def split_sentences(narration: str) -> list[str]:
    cleaned = (narration or "").strip()
    if not cleaned:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(cleaned) if p.strip()]
    return parts


def _merge_sentences(sentences: list[str]) -> list[str]:
    """Merge short sentences into ~3–6s scenes by word budget."""
    if not sentences:
        return []
    scenes: list[str] = []
    buf: list[str] = []
    buf_words = 0
    for sentence in sentences:
        w = count_words(sentence)
        if not buf:
            buf = [sentence]
            buf_words = w
            continue
        if buf_words < MIN_SCENE_WORDS or (
            buf_words + w <= MAX_SCENE_WORDS and buf_words < MAX_SCENE_WORDS
        ):
            buf.append(sentence)
            buf_words += w
            continue
        scenes.append(" ".join(buf))
        buf = [sentence]
        buf_words = w
    if buf:
        # If last buffer is tiny, merge into previous when possible
        if scenes and buf_words < MIN_SCENE_WORDS:
            scenes[-1] = f"{scenes[-1]} {' '.join(buf)}"
        else:
            scenes.append(" ".join(buf))
    return scenes


def purpose_for_index(index: int, total: int) -> ScenePurpose:
    if total <= 0:
        return "explanation"
    if total == 1:
        return "explanation"
    ratio = index / max(total - 1, 1)
    if index == 0:
        return "hook"
    if index == total - 1:
        return "cta"
    if index == total - 2 and total >= 4:
        return "perspective_shift"
    if ratio < 0.18:
        return "question"
    if ratio < 0.62:
        return "explanation"
    if ratio < 0.82:
        return "twist"
    return "perspective_shift"


def visual_for_purpose(purpose: ScenePurpose) -> tuple[str, str, str, str]:
    """Return suggested_visual, suggested_motion, on_screen_text, transition."""
    table: dict[ScenePurpose, tuple[str, str, str, str]] = {
        "hook": (
            "Single strong hero image matching the opening line; generous negative space",
            "Static or very slow push-in (max ~105%)",
            "Optional ≤6-word topic chip",
            "Soft fade or invisible cut",
        ),
        "question": (
            "Establish the phenomenon; light context plate",
            "Gentle hold; minimal motion",
            "Short question label if helpful (≤42 chars)",
            "Invisible cut",
        ),
        "explanation": (
            "Clearest teaching visual — diagram or mechanism illustration",
            "Build diagram parts in VO order; one element at a time",
            "Sparse structure labels (≤3 words)",
            "Invisible cut or soft slide",
        ),
        "twist": (
            "Visual reframe of the model (not a jump scare)",
            "Subtle highlight / recolor; no crash zoom",
            "Calm callout only if myth correction needs text",
            "Soft fade",
        ),
        "perspective_shift": (
            "Ordinary-life afterimage (window bird, sky, blink, year)",
            "Hold still 3–5s; breathing room",
            "Minimal or no text — let VO carry",
            "Hold into CTA",
        ),
        "cta": (
            "Quiet brand lockup over afterimage",
            "Fade wordmark; no bell spam",
            "Optional soft end line",
            "Fade to end",
        ),
    }
    return table[purpose]


def format_timecode(seconds: float) -> str:
    whole = max(0, int(seconds))
    mins, secs = divmod(whole, 60)
    return f"{mins}:{secs:02d}"


def build_storyboard_scenes(
    narration: str, *, wpm: int = 150
) -> list[dict]:
    sentences = split_sentences(narration)
    chunks = _merge_sentences(sentences)
    if not chunks:
        return []

    words_per_scene = [max(1, count_words(c)) for c in chunks]
    # Scale durations to land near 60s while keeping 3–6s when possible
    raw_seconds = [(w / wpm) * 60.0 for w in words_per_scene]
    total_raw = sum(raw_seconds) or 1.0
    target_total = min(60.0, max(55.0, total_raw))
    scale = target_total / total_raw
    durations = [max(TARGET_SCENE_SECONDS_MIN, min(TARGET_SCENE_SECONDS_MAX, s * scale)) for s in raw_seconds]
    # Renormalize if clamp drifted total badly
    dur_sum = sum(durations) or 1.0
    durations = [d * (target_total / dur_sum) for d in durations]

    scenes: list[dict] = []
    t = 0.0
    total = len(chunks)
    for i, text in enumerate(chunks):
        purpose = purpose_for_index(i, total)
        visual, motion, ost, transition = visual_for_purpose(purpose)
        start = t
        end = t + durations[i]
        scenes.append(
            {
                "scene_number": i + 1,
                "time_range": f"{format_timecode(start)}–{format_timecode(end)}",
                "start_seconds": round(start, 2),
                "end_seconds": round(end, 2),
                "narration": text,
                "purpose": purpose,
                "suggested_visual": visual,
                "suggested_motion": motion,
                "suggested_on_screen_text": ost,
                "transition": transition,
            }
        )
        t = end
    return scenes


def wrap_caption_lines(text: str, *, max_chars: int = 42, max_lines: int = 2) -> list[str]:
    words = text.strip().split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    elif current and lines:
        # Truncate overflow into last line with ellipsis if needed
        overflow = current
        last = lines[-1]
        room = max_chars - len(last) - 1
        if room > 3:
            lines[-1] = f"{last} {overflow[: room - 1]}…"
        else:
            lines[-1] = (last[: max_chars - 1] + "…") if len(last) >= max_chars else last
    return lines[:max_lines]


def build_subtitle_segments(
    scenes: list[dict],
) -> list[dict]:
    """One caption block per sentence inside each scene, timed proportionally."""
    segments: list[dict] = []
    idx = 1
    for scene in scenes:
        narration = scene["narration"]
        sentences = split_sentences(narration) or [narration]
        start = float(scene["start_seconds"])
        end = float(scene["end_seconds"])
        span = max(0.01, end - start)
        weights = [max(1, count_words(s)) for s in sentences]
        weight_sum = sum(weights) or 1
        cursor = start
        for si, sentence in enumerate(sentences):
            frac = weights[si] / weight_sum
            seg_end = end if si == len(sentences) - 1 else cursor + span * frac
            lines = wrap_caption_lines(sentence)
            if not lines:
                continue
            segments.append(
                {
                    "index": idx,
                    "start_seconds": round(cursor, 2),
                    "end_seconds": round(seg_end, 2),
                    "text": " ".join(lines),
                    "lines": lines,
                }
            )
            idx += 1
            cursor = seg_end
    return segments


EMPHASIS_HINTS = re.compile(
    r"\b(not|never|still|unknown|mystery|twist|surprise|living|quietly|maybe)\b",
    re.IGNORECASE,
)


def emphasis_markers(narration: str) -> list[str]:
    markers: list[str] = []
    for sentence in split_sentences(narration):
        if EMPHASIS_HINTS.search(sentence) or sentence.endswith("?"):
            markers.append(sentence.strip())
    return markers[:8]


def pause_markers(scenes: list[dict]) -> list[str]:
    markers: list[str] = []
    for scene in scenes:
        purpose = scene["purpose"]
        if purpose in {"hook", "twist", "perspective_shift", "cta"}:
            markers.append(
                f"Scene {scene['scene_number']} ({purpose}): reflection/idea pause at {scene['time_range']}"
            )
    return markers


def pronunciation_notes(narration: str) -> list[str]:
    notes: list[str] = []
    lower = narration.lower()
    checks = [
        ("chicxulub", "Chicxulub ≈ CHEEK-shoo-loob — confirm with editorial before session"),
        ("wifi", "Wi‑Fi as why-fye (not spelled out)"),
        ("wi-fi", "Wi‑Fi as why-fye (not spelled out)"),
        ("spaghettification", "Speak slowly on first mention; no apology tone"),
        ("million", "Speak large numbers fully (e.g. sixty-six million)"),
    ]
    for needle, note in checks:
        if needle in lower:
            notes.append(note)
    if not notes:
        notes.append("Verify any rare scientific names with editorial before recording.")
    return notes
