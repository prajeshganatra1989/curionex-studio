"""Production package generator — planning export for Gold-eligible scripts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_versions.constants import VERSION_STATUS_APPROVED
from app.models.ai import AiGeneration
from app.models.content_version import ContentVersion
from app.models.knowledge_pack import KnowledgePack, KnowledgePackSection
from app.models.project import Project
from app.models.script import Script
from app.models.user import User
from app.production.package_schemas import (
    AssetChecklistItem,
    ProductionPackageEligibilityResponse,
    ProductionPackageKnowledgePackSummary,
    ProductionPackageMetadata,
    ProductionPackageProjectInfo,
    ProductionPackageQualityReviewSummary,
    ProductionPackageResponse,
    ProductionPackageScriptInfo,
    QaChecklistItem,
    ShotListItem,
    StoryboardScene,
    SubtitleSegment,
    VoicePackage,
    YouTubePackage,
)
from app.production.storyboard import (
    build_storyboard_scenes,
    build_subtitle_segments,
    count_words,
    emphasis_markers,
    pause_markers,
    pronunciation_notes,
)
from app.scripts.constants import SCRIPT_STATUS_APPROVED
from app.services import script_quality_service, script_service

GOLD_SCORE_THRESHOLD = 95.0
DEFAULT_WPM = 150
TARGET_DURATION_SECONDS = 60

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "as",
        "at",
        "by",
        "with",
        "from",
        "that",
        "this",
        "it",
        "we",
        "you",
        "your",
        "our",
        "why",
        "how",
        "what",
        "do",
        "does",
        "did",
        "not",
        "into",
        "about",
    }
)


class NotFoundError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class NotGoldApprovedError(Exception):
    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _doc_map(script: Script) -> dict[str, str]:
    return {
        d.document_type: (d.content or "")
        for d in sorted(script.documents, key=lambda x: x.position)
    }


def _kp_sections(db: Session, pack_id: UUID | None) -> dict[str, str]:
    if pack_id is None:
        return {}
    rows = list(
        db.scalars(
            select(KnowledgePackSection).where(
                KnowledgePackSection.knowledge_pack_id == pack_id
            )
        ).all()
    )
    return {r.key: (r.content or "") for r in rows}


def _latest_approved_version(
    db: Session, script_id: UUID
) -> ContentVersion | None:
    return db.scalar(
        select(ContentVersion)
        .where(
            ContentVersion.script_id == script_id,
            ContentVersion.status == VERSION_STATUS_APPROVED,
        )
        .order_by(ContentVersion.version_number.desc())
        .limit(1)
    )


def _review_score(generation: AiGeneration | None) -> float | None:
    if generation is None:
        return None
    structured = generation.structured_output_json or {}
    raw = structured.get("overall_score")
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def evaluate_gold_eligibility(
    db: Session, script: Script, *, actor: User
) -> ProductionPackageEligibilityResponse:
    approved_version = _latest_approved_version(db, script.id)
    has_approved = approved_version is not None
    score: float | None = None
    gate: str | None = None
    reason = "Script is not Gold-approved yet."

    if script.status == SCRIPT_STATUS_APPROVED:
        gate = "script_status_approved"
        reason = "Script status is approved."
    elif has_approved:
        gate = "content_version_approved"
        reason = "An approved content version exists."
    else:
        try:
            review = script_quality_service.get_latest_quality_review(
                db, script.id, actor=actor
            )
        except script_quality_service.ForbiddenError as exc:
            raise ForbiddenError(str(exc)) from exc
        except script_quality_service.NotFoundError:
            review = None
        score = _review_score(review)
        if score is not None and score >= GOLD_SCORE_THRESHOLD:
            gate = "quality_review_gold"
            reason = (
                f"Latest quality review overall_score {score:g} meets Gold "
                f"threshold ({GOLD_SCORE_THRESHOLD:g}+)."
            )

    eligible = gate is not None
    if not eligible:
        reason = (
            "Requires script status approved, an approved content version, "
            f"or a quality review overall_score ≥ {GOLD_SCORE_THRESHOLD:g}."
        )

    return ProductionPackageEligibilityResponse(
        eligible=eligible,
        reason=reason,
        gold_gate=gate,
        overall_score=score,
        script_status=script.status,
        has_approved_version=has_approved,
    )


def _quality_summary(
    db: Session, script: Script, *, actor: User
) -> ProductionPackageQualityReviewSummary:
    try:
        review = script_quality_service.get_latest_quality_review(
            db, script.id, actor=actor
        )
    except (script_quality_service.ForbiddenError, script_quality_service.NotFoundError):
        review = None
    if review is None:
        return ProductionPackageQualityReviewSummary(available=False)
    structured = review.structured_output_json or {}
    score = _review_score(review)
    return ProductionPackageQualityReviewSummary(
        available=True,
        generation_id=review.id,
        overall_score=score,
        quality_band=structured.get("quality_band"),
        recommended_next_action=structured.get("recommended_next_action"),
        gold_threshold_met=bool(score is not None and score >= GOLD_SCORE_THRESHOLD),
    )


def _shot_list(scenes: list[dict]) -> list[ShotListItem]:
    shots: list[ShotListItem] = []
    n = 1
    for scene in scenes:
        purpose = scene["purpose"]
        if purpose in {"explanation", "twist"}:
            shots.append(
                ShotListItem(
                    shot_number=n,
                    scene_number=scene["scene_number"],
                    asset_type="diagram",
                    description=f"Teaching visual for scene {scene['scene_number']}",
                    diagram=True,
                    animation=True,
                    priority="must",
                )
            )
            n += 1
            shots.append(
                ShotListItem(
                    shot_number=n,
                    scene_number=scene["scene_number"],
                    asset_type="illustration",
                    description=f"Supporting illustration — {purpose}",
                    illustration=True,
                    priority="should",
                )
            )
            n += 1
        elif purpose in {"hook", "perspective_shift"}:
            shots.append(
                ShotListItem(
                    shot_number=n,
                    scene_number=scene["scene_number"],
                    asset_type="stock",
                    description=f"Hero / afterimage plate — {purpose}",
                    stock=True,
                    priority="must",
                )
            )
            n += 1
        elif purpose == "cta":
            shots.append(
                ShotListItem(
                    shot_number=n,
                    scene_number=scene["scene_number"],
                    asset_type="text_overlay",
                    description="Quiet brand lockup / soft end card",
                    text_overlay=True,
                    priority="must",
                )
            )
            n += 1
        else:
            shots.append(
                ShotListItem(
                    shot_number=n,
                    scene_number=scene["scene_number"],
                    asset_type="illustration",
                    description=f"Context plate — {purpose}",
                    illustration=True,
                    priority="should",
                )
            )
            n += 1
    return shots


def _asset_checklist(shots: list[ShotListItem]) -> list[AssetChecklistItem]:
    needs_illustration = any(s.illustration for s in shots)
    needs_stock = any(s.stock for s in shots)
    needs_diagram = any(s.diagram for s in shots)
    needs_animation = any(s.animation for s in shots)
    needs_text = any(s.text_overlay for s in shots)
    return [
        AssetChecklistItem(
            id="ai_illustration",
            label="AI Illustration",
            category="visual",
            required=needs_illustration,
            notes="Planning only — generate later via approved pipeline",
        ),
        AssetChecklistItem(
            id="stock_footage",
            label="Stock Footage",
            category="visual",
            required=needs_stock,
        ),
        AssetChecklistItem(
            id="diagram",
            label="Diagram",
            category="visual",
            required=needs_diagram,
        ),
        AssetChecklistItem(
            id="icon",
            label="Icon",
            category="visual",
            required=False,
        ),
        AssetChecklistItem(
            id="animation",
            label="Motion / Animation",
            category="visual",
            required=needs_animation,
        ),
        AssetChecklistItem(
            id="text_overlay",
            label="Text Overlay / End Card",
            category="visual",
            required=needs_text,
        ),
        AssetChecklistItem(
            id="sound_effect",
            label="Sound Effect",
            category="audio",
            required=False,
            notes="Prefer silence over whoosh spam (Production Blueprint)",
        ),
        AssetChecklistItem(
            id="background_music",
            label="Background Music",
            category="audio",
            required=False,
            notes="Sparse bed or none",
        ),
    ]


def _keywords_from_title(title: str) -> list[str]:
    words = [
        w.lower()
        for w in re.findall(r"[A-Za-z][A-Za-z0-9'-]*", title)
        if w.lower() not in STOPWORDS and len(w) > 2
    ]
    # preserve order unique
    seen: set[str] = set()
    out: list[str] = []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    base = out[:8]
    extras = ["science", "explained", "curiosity", "curionex", "shorts"]
    for e in extras:
        if e not in seen:
            base.append(e)
    return base[:12]


def _youtube_package(script: Script, master: str, angle: str | None) -> YouTubePackage:
    title = script.title.strip()
    if len(title) > 70:
        title = title[:67].rstrip() + "…"
    desc_parts = [
        script.title.strip(),
        "",
        (script.description or "").strip() or "A Curionex Short — curiosity, clearly explained.",
        "",
    ]
    if angle and angle.strip():
        desc_parts.extend(["Angle", angle.strip()[:500], ""])
    desc_parts.extend(
        [
            "Sources and claims follow Curionex Editorial Bible integrity rules.",
            "",
            "#Curionex #Science #Explained",
        ]
    )
    keywords = _keywords_from_title(script.title)
    hashtags = [
        "#Curionex",
        "#ScienceShorts",
        "#LearnOnYouTube",
        *[f"#{k.capitalize()}" for k in keywords[:4]],
    ]
    return YouTubePackage(
        title=title,
        description="\n".join(desc_parts).strip(),
        keywords=keywords,
        hashtags=hashtags,
        category="Education",
        thumbnail_concept=(
            "Calm single-subject 9:16 frame matching the hook image; "
            "minimal text (≤6 words); no shock face; brand accent sparingly."
        ),
    )


def _qa_package() -> list[QaChecklistItem]:
    items = [
        ("editorial", "Single takeaway is clear; ending is perspective shift, not summary"),
        ("editorial", "Myths corrected without humiliation"),
        ("voice", "Pacing comfortable; ending reflective (Voice Bible)"),
        ("voice", "No trailer energy in first 3 seconds"),
        ("graphics", "One idea on screen; labels match evidence layers"),
        ("graphics", "Safe margins and caption contrast OK"),
        ("timing", "Final cut 55–60 seconds; CTA ≤ last ~3s"),
        ("timing", "Storyboard scenes roughly 3–6 seconds"),
        ("brand", "Mute-picture test feels Curionex (calm, premium)"),
        ("brand", "Soft CTA — no smash-subscribe energy"),
        ("scientific_integrity", "No invented stats; unknowns not solved visually"),
        ("scientific_integrity", "Hypothesis vs established treated honestly"),
    ]
    return [
        QaChecklistItem(id=f"qa_{i+1}", domain=domain, label=label)  # type: ignore[arg-type]
        for i, (domain, label) in enumerate(items)
    ]


def generate_production_package(
    db: Session,
    script_id: UUID,
    *,
    actor: User,
) -> ProductionPackageResponse:
    try:
        script = script_service.get_script_for_user(db, script_id, actor)
    except script_service.NotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except script_service.ForbiddenError as exc:
        raise ForbiddenError(str(exc)) from exc

    eligibility = evaluate_gold_eligibility(db, script, actor=actor)
    if not eligibility.eligible or not eligibility.gold_gate:
        raise NotGoldApprovedError(eligibility.reason, reason="not_gold_approved")

    project = db.get(Project, script.project_id)
    if project is None:
        raise NotFoundError("Project not found.")

    docs = _doc_map(script)
    master = docs.get("master_script", "").strip()
    if not master:
        raise NotGoldApprovedError(
            "Master Script is empty — cannot build a production package.",
            reason="empty_master_script",
        )

    pack: KnowledgePack | None = None
    if script.knowledge_pack_id:
        pack = db.get(KnowledgePack, script.knowledge_pack_id)
    sections = _kp_sections(db, script.knowledge_pack_id)

    scenes_raw = build_storyboard_scenes(master, wpm=DEFAULT_WPM)
    storyboard = [StoryboardScene.model_validate(s) for s in scenes_raw]
    shots = _shot_list(scenes_raw)
    subtitles = [
        SubtitleSegment.model_validate(s) for s in build_subtitle_segments(scenes_raw)
    ]
    word_count = count_words(master)
    est = max(1, round((word_count / DEFAULT_WPM) * 60)) if word_count else 0

    quality = _quality_summary(db, script, actor=actor)

    return ProductionPackageResponse(
        project=ProductionPackageProjectInfo(
            id=project.id,
            project_code=project.project_code,
            name=project.name,
            status=project.status,
            description=project.description,
        ),
        script=ProductionPackageScriptInfo(
            id=script.id,
            script_code=script.script_code,
            title=script.title,
            status=script.status,
            description=script.description,
            knowledge_pack_id=script.knowledge_pack_id,
            project_id=script.project_id,
        ),
        knowledge_pack=ProductionPackageKnowledgePackSummary(
            id=pack.id if pack else None,
            name=pack.name if pack else None,
            status=pack.status if pack else None,
            description=pack.description if pack else None,
            facts=sections.get("facts") or None,
            sources=sections.get("sources") or None,
            content_angle=sections.get("content_angle") or None,
            key_insights=sections.get("key_insights") or None,
        ),
        discovery_brief=docs.get("discovery_brief", ""),
        story_spine=docs.get("story_spine", ""),
        master_script=master,
        quality_review=quality,
        production_metadata=ProductionPackageMetadata(
            generated_at=datetime.now(UTC),
            gold_gate=eligibility.gold_gate,
            target_duration_seconds=TARGET_DURATION_SECONDS,
            recommended_wpm=DEFAULT_WPM,
        ),
        storyboard=storyboard,
        shot_list=shots,
        asset_checklist=_asset_checklist(shots),
        voice_package=VoicePackage(
            estimated_duration_seconds=est,
            word_count=word_count,
            recommended_wpm=DEFAULT_WPM,
            pause_markers=pause_markers(scenes_raw),
            emphasis_markers=emphasis_markers(master),
            pronunciation_notes=pronunciation_notes(master),
        ),
        subtitle_package=subtitles,
        youtube_package=_youtube_package(
            script, master, sections.get("content_angle")
        ),
        qa_package=_qa_package(),
    )
