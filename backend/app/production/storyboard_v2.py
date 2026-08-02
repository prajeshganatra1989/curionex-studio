"""Production Storyboard V2 — rich scene-by-scene planning cards."""

from __future__ import annotations

import re
from typing import Literal

from app.production.storyboard import ScenePurpose, build_storyboard_scenes

VisualType = Literal[
    "AI Illustration",
    "Stock Footage",
    "3D Animation",
    "Diagram",
    "Timeline",
    "Map",
    "Historical Photo",
    "UI Animation",
    "Macro",
    "Space",
    "Medical Illustration",
    "Icon Animation",
]

CameraMovement = Literal[
    "Static",
    "Push",
    "Pull",
    "Pan",
    "Orbit",
    "Parallax",
    "No movement",
]

TransitionKind = Literal[
    "Fade",
    "Cut",
    "Cross Dissolve",
    "Match Cut",
    "Zoom",
    "Slide",
]

MusicMood = Literal[
    "Curious",
    "Calm",
    "Epic",
    "Reflective",
    "Wonder",
]

TextPosition = Literal[
    "top",
    "center",
    "bottom",
    "lower_third",
    "none",
]

ViewerEmotion = Literal[
    "curiosity",
    "wonder",
    "clarity",
    "surprise",
    "calm_awe",
    "belonging",
]

_SPACE = re.compile(
    r"\b(space|galaxy|planet|star|black hole|orbit|cosmos|universe|moon)\b",
    re.I,
)
_MEDICAL = re.compile(
    r"\b(brain|blood|heart|cell|neuron|body|blink|yawn|eye|medical)\b", re.I
)
_MAP = re.compile(r"\b(earth|continent|ocean|map|country|city|world)\b", re.I)
_TIME = re.compile(
    r"\b(million|billion|year|century|timeline|history|ago|ancient)\b", re.I
)
_MACRO = re.compile(r"\b(magnet|paperclip|dust|grain|drop|micro|tiny|atom)\b", re.I)
_UI = re.compile(r"\b(wifi|wi-fi|screen|app|phone|interface|button)\b", re.I)
_HISTORICAL = re.compile(
    r"\b(dinosaur|fossil|ancient|egypt|rome|victorian|photograph)\b", re.I
)


def _visual_type(purpose: ScenePurpose, narration: str) -> VisualType:
    if _SPACE.search(narration):
        return "Space"
    if _MEDICAL.search(narration):
        return "Medical Illustration"
    if _MAP.search(narration):
        return "Map"
    if _TIME.search(narration):
        return "Timeline"
    if _HISTORICAL.search(narration):
        return "Historical Photo"
    if _UI.search(narration):
        return "UI Animation"
    if _MACRO.search(narration):
        return "Macro"
    table: dict[ScenePurpose, VisualType] = {
        "hook": "Stock Footage",
        "question": "AI Illustration",
        "explanation": "Diagram",
        "twist": "3D Animation",
        "perspective_shift": "AI Illustration",
        "cta": "Icon Animation",
    }
    return table[purpose]


def _camera(purpose: ScenePurpose, visual: VisualType) -> CameraMovement:
    if purpose == "hook":
        return "Push"
    if purpose == "question":
        return "Static"
    if purpose == "explanation":
        if visual in {"Diagram", "Timeline", "Map"}:
            return "Pan"
        return "Parallax"
    if purpose == "twist":
        return "Orbit" if visual == "3D Animation" else "Pull"
    if purpose == "perspective_shift":
        return "No movement"
    return "Static"


def _transition(purpose: ScenePurpose, index: int, total: int) -> TransitionKind:
    if index == 0:
        return "Fade"
    if purpose == "twist":
        return "Match Cut"
    if purpose == "perspective_shift":
        return "Cross Dissolve"
    if purpose == "cta" or index == total - 1:
        return "Fade"
    if purpose == "explanation":
        return "Slide"
    if purpose == "question":
        return "Cut"
    return "Cut"


def _music(purpose: ScenePurpose) -> MusicMood:
    table: dict[ScenePurpose, MusicMood] = {
        "hook": "Curious",
        "question": "Curious",
        "explanation": "Calm",
        "twist": "Wonder",
        "perspective_shift": "Reflective",
        "cta": "Reflective",
    }
    return table[purpose]


def _emotion(purpose: ScenePurpose) -> ViewerEmotion:
    table: dict[ScenePurpose, ViewerEmotion] = {
        "hook": "curiosity",
        "question": "curiosity",
        "explanation": "clarity",
        "twist": "surprise",
        "perspective_shift": "calm_awe",
        "cta": "belonging",
    }
    return table[purpose]


def _scene_goal(purpose: ScenePurpose) -> str:
    table: dict[ScenePurpose, str] = {
        "hook": "Open with a concrete moment that earns attention without trailer energy",
        "question": "Frame the core question the viewer already feels",
        "explanation": "Teach one mechanism clearly — one idea on screen",
        "twist": "Reframe the model calmly; correct without humiliation",
        "perspective_shift": "Leave an ordinary-life afterimage that sticks",
        "cta": "Soft brand close — invite, don't smash",
    }
    return table[purpose]


def _animation(purpose: ScenePurpose, visual: VisualType) -> str:
    if visual == "Diagram":
        return "Reveal diagram parts in VO order; one element at a time"
    if visual == "Timeline":
        return "Advance timeline marker with narration; no jitter"
    if visual == "3D Animation":
        return "Slow orbit or assemble; keep physics readable"
    if visual == "Icon Animation":
        return "Fade brand mark / soft icon settle"
    if visual == "UI Animation":
        return "Subtle UI highlight matching the explained action"
    if purpose == "hook":
        return "Gentle push-in on hero subject (max ~105%)"
    if purpose == "perspective_shift":
        return "Hold still 3–5s; breathing room"
    return "Minimal motion; prioritize readability"


def _text_and_position(
    purpose: ScenePurpose, on_screen_v1: str
) -> tuple[str, TextPosition]:
    if purpose in {"perspective_shift", "cta"}:
        if purpose == "cta":
            return ("Optional soft end line", "bottom")
        return ("", "none")
    if purpose == "hook":
        return (on_screen_v1 or "Optional ≤6-word topic chip", "top")
    if purpose == "explanation":
        return (on_screen_v1 or "Sparse structure labels", "lower_third")
    if purpose == "question":
        return (on_screen_v1 or "Short question label", "center")
    return (on_screen_v1 or "", "lower_third")


def _asset_required(visual: VisualType) -> str:
    return visual


def _sfx(purpose: ScenePurpose, narration: str, visual: VisualType) -> str:
    lower = narration.lower()
    if "heart" in lower or "pulse" in lower:
        return "Heartbeat"
    if visual == "Space" or _SPACE.search(narration):
        return "Space ambience"
    if "page" in lower or "book" in lower or "paper" in lower:
        return "Paper"
    if "wind" in lower or "air" in lower:
        return "Wind"
    if purpose == "twist":
        return "Whoosh"
    if purpose == "hook" and "page" not in lower:
        return "None"
    if purpose in {"explanation", "question", "perspective_shift", "cta"}:
        return "None"
    return "None"


def _notes(purpose: ScenePurpose, visual: VisualType) -> str:
    bits = [
        f"Purpose: {purpose.replace('_', ' ')}.",
        f"Mute-picture test: {visual} must read without VO.",
    ]
    if purpose == "cta":
        bits.append("Keep CTA under ~3s; no bell spam.")
    if visual == "Diagram":
        bits.append("Labels must match evidence layers in Knowledge Pack.")
    return " ".join(bits)


def enrich_scene_v2(scene: dict, *, index: int, total: int) -> dict:
    """Upgrade a v1 storyboard scene dict into a v2 planning card."""
    purpose: ScenePurpose = scene["purpose"]
    narration = scene["narration"]
    visual = _visual_type(purpose, narration)
    camera = _camera(purpose, visual)
    transition = _transition(purpose, index, total)
    on_screen, text_pos = _text_and_position(
        purpose, scene.get("suggested_on_screen_text", "")
    )
    start = float(scene["start_seconds"])
    end = float(scene["end_seconds"])
    return {
        "scene_number": scene["scene_number"],
        "start_time": round(start, 2),
        "end_time": round(end, 2),
        "duration": round(end - start, 2),
        "narration": narration,
        "scene_goal": _scene_goal(purpose),
        "viewer_emotion": _emotion(purpose),
        "visual_type": visual,
        "camera_movement": camera,
        "transition": transition,
        "animation_suggestion": _animation(purpose, visual),
        "on_screen_text": on_screen,
        "text_position": text_pos,
        "asset_required": _asset_required(visual),
        "music_mood": _music(purpose),
        "sound_effects": _sfx(purpose, narration, visual),
        "notes": _notes(purpose, visual),
        "purpose": purpose,
    }


def build_storyboard_v2(narration: str, *, wpm: int = 150) -> list[dict]:
    """Build full Storyboard V2 from master narration (reuses v1 scene timing)."""
    base = build_storyboard_scenes(narration, wpm=wpm)
    total = len(base)
    return [enrich_scene_v2(scene, index=i, total=total) for i, scene in enumerate(base)]


def storyboard_v2_to_markdown(
    scenes: list[dict],
    *,
    title: str = "Production Storyboard V2",
) -> str:
    """Export storyboard v2 scenes as Markdown for copy/paste."""
    lines = [f"# {title}", ""]
    for scene in scenes:
        n = scene["scene_number"]
        lines.append(f"## Scene {n}")
        lines.append("")
        lines.append(
            f"- **Time:** {scene['start_time']:.2f}s – {scene['end_time']:.2f}s "
            f"({scene['duration']:.2f}s)"
        )
        lines.append(f"- **Scene goal:** {scene['scene_goal']}")
        lines.append(f"- **Viewer emotion:** {scene['viewer_emotion']}")
        lines.append(f"- **Visual type:** {scene['visual_type']}")
        lines.append(f"- **Camera:** {scene['camera_movement']}")
        lines.append(f"- **Transition:** {scene['transition']}")
        lines.append(f"- **Animation:** {scene['animation_suggestion']}")
        lines.append(f"- **On-screen text:** {scene['on_screen_text'] or '—'}")
        lines.append(f"- **Text position:** {scene['text_position']}")
        lines.append(f"- **Asset required:** {scene['asset_required']}")
        lines.append(f"- **Music mood:** {scene['music_mood']}")
        lines.append(f"- **SFX:** {scene['sound_effects']}")
        lines.append(f"- **Notes:** {scene['notes']}")
        lines.append("")
        lines.append("**Narration**")
        lines.append("")
        lines.append(scene["narration"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
