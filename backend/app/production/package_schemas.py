"""Production package API schemas (planning export — no media generation)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


AssetType = Literal[
    "illustration",
    "stock",
    "diagram",
    "animation",
    "text_overlay",
    "icon",
    "map",
    "space_imagery",
    "other",
]

ScenePurpose = Literal[
    "hook",
    "question",
    "explanation",
    "twist",
    "perspective_shift",
    "cta",
]


class ProductionPackageProjectInfo(BaseModel):
    id: UUID
    project_code: str
    name: str
    status: str
    description: str | None = None


class ProductionPackageScriptInfo(BaseModel):
    id: UUID
    script_code: str
    title: str
    status: str
    description: str | None = None
    knowledge_pack_id: UUID | None = None
    project_id: UUID


class ProductionPackageKnowledgePackSummary(BaseModel):
    id: UUID | None = None
    name: str | None = None
    status: str | None = None
    description: str | None = None
    facts: str | None = None
    sources: str | None = None
    content_angle: str | None = None
    key_insights: str | None = None


class ProductionPackageQualityReviewSummary(BaseModel):
    available: bool = False
    generation_id: UUID | None = None
    overall_score: float | None = None
    quality_band: str | None = None
    recommended_next_action: str | None = None
    gold_threshold_met: bool = False


class ProductionPackageMetadata(BaseModel):
    generated_at: datetime
    gold_gate: str
    target_duration_seconds: int = 60
    recommended_wpm: int = 150
    format: str = "youtube_shorts_9x16"
    blueprint_version: str = "1.0"
    voice_bible_version: str = "1.0"
    editorial_bible_version: str = "1.0"
    notes: str = (
        "Planning package only — no media generation, ElevenLabs, or ZIP export."
    )


class StoryboardScene(BaseModel):
    scene_number: int
    time_range: str
    start_seconds: float
    end_seconds: float
    narration: str
    purpose: ScenePurpose
    suggested_visual: str
    suggested_motion: str
    suggested_on_screen_text: str
    transition: str


class ShotListItem(BaseModel):
    shot_number: int
    scene_number: int
    asset_type: AssetType
    description: str
    illustration: bool = False
    stock: bool = False
    diagram: bool = False
    animation: bool = False
    text_overlay: bool = False
    priority: Literal["must", "should", "nice"] = "should"


class AssetChecklistItem(BaseModel):
    id: str
    label: str
    category: str
    required: bool = False
    notes: str | None = None


class VoicePackage(BaseModel):
    estimated_duration_seconds: int
    word_count: int
    recommended_wpm: int
    pause_markers: list[str]
    emphasis_markers: list[str]
    pronunciation_notes: list[str]
    persona_hint: str = "Primary Curionex Narrator"


class SubtitleSegment(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    text: str
    lines: list[str]


class YouTubePackage(BaseModel):
    title: str
    description: str
    keywords: list[str]
    hashtags: list[str]
    category: str
    thumbnail_concept: str


class QaChecklistItem(BaseModel):
    id: str
    domain: Literal[
        "editorial",
        "voice",
        "graphics",
        "timing",
        "brand",
        "scientific_integrity",
    ]
    label: str
    checked: bool = False


class ProductionPackageResponse(BaseModel):
    project: ProductionPackageProjectInfo
    script: ProductionPackageScriptInfo
    knowledge_pack: ProductionPackageKnowledgePackSummary
    discovery_brief: str
    story_spine: str
    master_script: str
    quality_review: ProductionPackageQualityReviewSummary
    production_metadata: ProductionPackageMetadata
    storyboard: list[StoryboardScene]
    shot_list: list[ShotListItem]
    asset_checklist: list[AssetChecklistItem]
    voice_package: VoicePackage
    subtitle_package: list[SubtitleSegment]
    youtube_package: YouTubePackage
    qa_package: list[QaChecklistItem]


class ProductionPackageEligibilityResponse(BaseModel):
    eligible: bool
    reason: str
    gold_gate: str | None = None
    overall_score: float | None = None
    script_status: str
    has_approved_version: bool = False
