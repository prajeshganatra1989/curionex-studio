# Production Package Generator

**Version:** 1.0  
**Status:** Production Phase · Planning export only  
**Related:** [008-production-blueprint-v1.md](./008-production-blueprint-v1.md) · [007-voice-narration-bible-v1.md](./007-voice-narration-bible-v1.md) · [../editorial/020-editorial-bible-v1.md](../editorial/020-editorial-bible-v1.md)

## Purpose

Generate a **complete production planning package** for a Gold-eligible script.

This is **not** video rendering, image generation, ElevenLabs synthesis, or ZIP export.

## API

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/scripts/{script_id}/production-package/eligibility` | `scripts.view` |
| `POST` | `/scripts/{script_id}/production-package` | `scripts.view` |

### Gold gate

Eligible when **any** of:

1. Script `status == approved`
2. An approved `ContentVersion` exists for the script
3. Latest AI quality review `overall_score >= 95` (Editorial Bible Gold threshold)

Otherwise `POST` returns **422** with `code: not_gold_approved`.

### Response (JSON)

- Project / script information  
- Knowledge Pack summary (facts, sources, angle, insights when linked)  
- Discovery Brief, Story Spine, Master Script bodies  
- Quality review summary  
- Production metadata (gate, WPM, blueprint versions)  
- **Storyboard** — scenes ~3–6s with visual/motion/text/transition suggestions  
- **Storyboard V2** — full production cards (goal, emotion, visual type, camera, music, SFX, notes)  
- **Shot list** — asset types + priority  
- **Asset checklist**  
- **Voice package** — duration, WPM, pauses, emphasis, pronunciation  
- **Subtitle package** — ≤2 lines, ≤42 chars/line  
- **YouTube package** — title, description, keywords, hashtags, category, thumbnail concept  
- **QA package** — editorial / voice / graphics / timing / brand / integrity  

## Frontend

- Script workspace header button **Generate Production Package** (only when eligible)
- Page: `/projects/{projectId}/scripts/{scriptId}/production-package`
- Tabs: Overview · Storyboard · Storyboard V2 · Shot List · Assets · Voice · Subtitles · YouTube · QA

## Out of scope (this release)

- ZIP download  
- AI image / video generation  
- ElevenLabs calls  
- Auto-publish  

## Implementation map

| Layer | Path |
|-------|------|
| Schemas | `backend/app/production/package_schemas.py` |
| Storyboard helpers | `backend/app/production/storyboard.py` |
| Service | `backend/app/services/production_package_service.py` |
| Routes | `backend/app/api/routes/scripts.py` |
| UI | `frontend/src/components/scripts/production-package-page.tsx` |
| Tests | `backend/tests/test_production_package.py` |
