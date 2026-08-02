# Story Spine Generation

## Purpose

Prompt purpose code: `script.story_spine.draft`  
Seeded name: **Story Spine Draft**

Turns an approved Discovery Brief into beat-by-beat narrative structure for short-form educational video.

## Prerequisite

Discovery Brief document must exist and have non-empty content. Otherwise queueing fails with `missing_prerequisite` / HTTP 422 listing `discovery_brief`.

## Variables

`project_code`, `project_title`, `script_title`,  
`discovery_brief`,  
`knowledge_pack_facts`, `knowledge_pack_sources`, `knowledge_pack_key_insights`,  
`language`, `tone`, `target_duration_seconds`,  
`target_word_count_low`, `target_word_count_target`, `target_word_count_high`,  
`brand_voice`, `quality_requirements`

Word-count bounds come from duration × WPM with ±10% tolerance (same helper as Master Script).

## Structured schema

```json
{
  "hook": "string",
  "setup": "string",
  "curiosity_gap": "string",
  "progression": [
    {
      "beat": 1,
      "purpose": "string",
      "content": "string",
      "estimated_seconds": 1
    }
  ],
  "core_explanation": "string",
  "reveal_or_reframe": "string",
  "ending": "string",
  "call_to_action": "string",
  "visual_rhythm_notes": ["string"],
  "retention_risks": ["string"],
  "claims_requiring_verification": ["string"],
  "estimated_total_seconds": 60
}
```

### Beats

- `progression` beats must be consecutive integers starting at `1`  
- Each beat `estimated_seconds` must be ≥ 1  
- Beats are sorted by `beat` on parse  

## Conversion

Apply writes plain text sections: `HOOK`, `SETUP`, `CURIOSITY GAP`, `STORY BEATS` (numbered `[purpose] (Ns)` blocks), `CORE EXPLANATION`, `REVEAL / REFRAME`, `ENDING`, `CALL TO ACTION`, `VISUAL RHYTHM NOTES`, `RETENTION RISKS`, `CLAIMS REQUIRING VERIFICATION`, `ESTIMATED DURATION`.

## Quality

- Stay faithful to the Discovery Brief; do not introduce unsupported facts or claims  
- Flag retention risks and claims still needing verification  
- Avoid sensationalism and false certainty  
- Return only the required structured schema  
