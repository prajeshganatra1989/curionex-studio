# Production Storyboard Generator

**Version:** 1.0  
**Status:** Production Phase · Planning only  
**Related:** [009-production-package.md](./009-production-package.md) · [008-production-blueprint-v1.md](./008-production-blueprint-v1.md)

## Purpose

Extend the Production Package with **Storyboard V2** — a complete scene-by-scene production storyboard for Gold-approved scripts.

This is planning only: **no** AI image generation, video rendering, ElevenLabs, or ZIP export.

## API

`POST /scripts/{script_id}/production-package` now includes:

```json
"storyboard_v2": [ /* StoryboardV2Scene[] */ ]
```

v1 `storyboard` is unchanged (compat table for shot list / subtitles).

### Gold gate

Same as Production Package Generator (script approved, approved content version, or quality score ≥ 95).

## Scene card fields

| Field | Notes |
|-------|--------|
| Scene Number | 1-based |
| Start / End Time | Seconds |
| Duration | Target ~3–6s per scene |
| Narration | Scene VO chunk |
| Scene Goal | Purpose-driven production intent |
| Viewer Emotion | curiosity · wonder · clarity · surprise · calm_awe · belonging |
| Visual Type | See vocabulary below |
| Camera Movement | Static · Push · Pull · Pan · Orbit · Parallax · No movement |
| Transition | Fade · Cut · Cross Dissolve · Match Cut · Zoom · Slide |
| Animation Suggestion | Motion note for editors |
| On-screen Text | Caption / label suggestion |
| Text Position | top · center · bottom · lower_third · none |
| Asset Required | Primary asset class for the scene |
| Music Mood | Curious · Calm · Epic · Reflective · Wonder |
| Sound Effects | Meaningful only (else `None`) |
| Notes | Mute-picture / integrity reminders |

## Visual types

AI Illustration · Stock Footage · 3D Animation · Diagram · Timeline · Map · Historical Photo · UI Animation · Macro · Space · Medical Illustration · Icon Animation

Keyword heuristics (space, medical, map, timeline, etc.) refine type; otherwise purpose defaults apply.

## Frontend

- Tab: **Storyboard V2** on `/projects/{projectId}/scripts/{scriptId}/production-package`
- Timeline rail + per-scene cards
- **Copy Markdown** / **Export Markdown** (`.md` download)

## Implementation map

| Layer | Path |
|-------|------|
| Schemas | `backend/app/production/package_schemas.py` (`StoryboardV2Scene`) |
| Generator | `backend/app/production/storyboard_v2.py` |
| Service | `backend/app/services/production_package_service.py` |
| UI | `frontend/src/components/scripts/production-package-page.tsx` |
| Tests | `backend/tests/test_production_package.py`, `frontend/src/__tests__/production-package-page.test.tsx` |
| Spec | this document |

## Out of scope

- Media generation  
- Rendered storyboard frames  
- ZIP / NLE project export  
