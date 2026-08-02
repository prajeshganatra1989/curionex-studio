# Master Script Generation

## Purpose

Prompt purpose code: `script.master_script.draft`  
Seeded name: **Master Script Draft**

Final spoken narration for a short-form educational video, built from Discovery Brief and Story Spine.

## Prerequisites

Both must be non-empty:

1. Discovery Brief  
2. Story Spine  

Otherwise queueing fails with `missing_prerequisite` listing the missing types.

## Variables

`project_code`, `project_title`, `script_title`,  
`discovery_brief`, `story_spine`,  
`knowledge_pack_facts`, `knowledge_pack_sources`,  
`claims_requiring_verification` (extracted from the Discovery Brief `CLAIMS REQUIRING VERIFICATION` section when present),  
`language`, `tone`,  
`target_duration_seconds`, `target_words_per_minute`,  
`target_word_count_low`, `target_word_count_target`, `target_word_count_high`,  
`brand_voice`, `quality_requirements`

Defaults when unset: duration **60** seconds, **150** WPM (from `ai_settings` or constants).

## Narration schema

```json
{
  "title": "string",
  "narration": "string",
  "hook": "string",
  "ending": "string",
  "estimated_word_count": 0,
  "estimated_duration_seconds": 60,
  "on_screen_keywords": ["string"],
  "claims_requiring_verification": ["string"],
  "editor_notes": ["string"],
  "quality_checks": {
    "single_core_idea": true,
    "clear_hook": true,
    "clear_payoff": true,
    "duration_target_met": true
  }
}
```

Narration is meant to be read aloud — natural spoken rhythm, no stage directions inside the narration text.

## Duration / WPM

Target word count = round((duration_seconds / 60) × WPM).

Acceptable range: **±10%** of target (`DURATION_WORD_COUNT_TOLERANCE = 0.10`). Low bound is at least 1.

## One repair attempt

After the primary structured generation, if narration word count is outside `[low, high]`:

1. At most **one** follow-up provider call (`MASTER_SCRIPT_MAX_REPAIR_ATTEMPTS = 1`) asks for a duration-only rewrite  
2. Repair tokens and estimated cost are added to the generation totals  
3. Job still **completes** if length remains off — a warning is stored (no unlimited retries; job does not fail solely for duration mismatch)

## Narration-only apply

`master_script_to_plain_text` writes **only** `narration.trim()` into the Master Script document body.

Structured fields (`title`, `hook`, `ending`, keywords, editor notes, quality checks) remain on the generation for review; they are not merged into the document on apply.
