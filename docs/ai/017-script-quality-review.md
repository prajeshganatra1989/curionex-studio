# Script Quality Review

## Purpose

Prompt purpose code: `script.quality_review`  
Seeded name: **Script Quality Review**

Advisory editorial review of Master Script narration for short-form educational video. The model scores dimensions, flags priority issues and factual risks, and suggests targeted rewrites. **AI never approves content** and never auto-writes the Script Document.

## Prerequisites

- Master Script must be **non-empty** (manual paste or prior AI apply both accepted).
- Discovery Brief and Story Spine are **optional**. When empty, the job still runs and context warnings are attached (reduced confidence on alignment dimensions).

Empty Master Script → HTTP 422 (no provider call).

## Variables

`project_code`, `project_title`, `script_code`, `script_title`,  
`language`, `target_duration_seconds`, `target_words_per_minute`,  
`estimated_word_count`, `estimated_duration_seconds`,  
`brand_voice`, `quality_requirements`,  
`knowledge_pack_facts`, `knowledge_pack_sources`,  
`knowledge_pack_content_angle`, `knowledge_pack_key_insights`,  
`discovery_brief`, `story_spine`, `master_script`,  
`context_warnings`, `max_priority_issues`

Defaults when unset: duration **60** seconds, **150** WPM (from `ai_settings` or constants).

## Job lifecycle

`POST /scripts/{script_id}/ai-quality-reviews`

1. Seed / resolve prompt purpose `script.quality_review` + active version  
2. Resolve OpenAI model  
3. Build variables + **input fingerprint** (master, discovery, spine, pack section hashes, brand voice, review policy, prompt version)  
4. Queue `AiJob` (`document_type=master_script`, purpose `script.quality_review`)  
5. Execute via `job_executor` with structured schema `script_quality_review`  
6. Parse → **server enrich** (weighted score, band, recommendation, deterministic pacing) → persist `AiGeneration`  

Master Script content is **not** modified when the review completes.

List: `GET /scripts/{script_id}/ai-quality-reviews`  
Latest: `GET /scripts/{script_id}/ai-quality-reviews/latest`

## Idempotency

`idempotency_key` is unique per requesting user + script + purpose. Replays return the existing job and do not call the provider again.

## Cancel

Queued jobs may be cancelled via `POST /ai/jobs/{id}/cancel` before execution (`execute_now=False` path / race). Terminal jobs reject cancel with HTTP 409.

## Human gate

Reviews are advisory:

| Signal | Meaning |
|--------|---------|
| `ai_approval` | Always `false` |
| `ready_for_human_review` | Recommendation is `human_review` or `ready_for_version` — still a human decision |
| `recommended_next_action` | `revise` \| `human_review` \| `ready_for_version` — never “approved” |

Critical factual risks and critical priority issues force `revise`. Factual claims always require human verification (see [019-factual-risk-review.md](019-factual-risk-review.md)).

## Suggestion apply

`POST /scripts/{script_id}/ai-quality-reviews/{generation_id}/suggestions/{issue_id}/apply`

Strategy: `replace_excerpt` only. Exact unique excerpt replace; rejects missing, ambiguous, or stale reviews. See [020-quality-suggestions.md](020-quality-suggestions.md).

## Related

- [018-quality-scoring.md](018-quality-scoring.md)
- [019-factual-risk-review.md](019-factual-risk-review.md)
- [020-quality-suggestions.md](020-quality-suggestions.md)
- [015-ai-input-fingerprints.md](015-ai-input-fingerprints.md)
- [011-script-draft-pipeline.md](011-script-draft-pipeline.md)
