# Discovery Brief Generation

## Purpose

Prompt purpose code: `script.discovery_brief.draft`  
Seeded name: **Discovery Brief Draft**

Defines topic, audience, and angle before narrative writing. Grounded in Knowledge Pack context when the script is linked to a pack; claims that still need verification are listed explicitly.

## Variables

`project_code`, `project_title`, `project_description`, `category`, `tags`,  
`knowledge_pack_research`, `knowledge_pack_facts`, `knowledge_pack_sources`,  
`knowledge_pack_audience`, `knowledge_pack_content_angle`, `knowledge_pack_key_insights`,  
`knowledge_pack_additional_context`,  
`script_title`, `script_description`,  
`language`, `tone`, `target_duration_seconds`,  
`brand_voice`, `quality_requirements`

Missing Knowledge Pack sections are filled with `(Not provided.)`.

## Dependencies

None on other script documents. Knowledge Pack is optional context (empty sections if unlinked).

## Structured schema

```json
{
  "topic": "string",
  "working_title": "string",
  "core_question": "string",
  "viewer_promise": "string",
  "target_audience": "string",
  "core_takeaway": "string",
  "content_angle": "string",
  "key_facts": ["string"],
  "claims_requiring_verification": ["string"],
  "source_notes": ["string"],
  "emotional_direction": "string",
  "visual_opportunities": ["string"],
  "risks_and_cautions": ["string"],
  "recommended_duration_seconds": 60
}
```

`additionalProperties` is forbidden. Empty list items are stripped on parse.

## Conversion headings

Apply writes plain text with these ALL-CAPS sections (lists as `-` bullets; empty lists become `- (none)`):

`TOPIC`, `WORKING TITLE`, `CORE QUESTION`, `VIEWER PROMISE`, `TARGET AUDIENCE`, `CORE TAKEAWAY`, `CONTENT ANGLE`, `KEY FACTS`, `CLAIMS REQUIRING VERIFICATION`, `SOURCE NOTES`, `EMOTIONAL DIRECTION`, `VISUAL OPPORTUNITIES`, `RISKS AND CAUTIONS`, `RECOMMENDED DURATION` (`N seconds`).

## Quality rules

Prompt instructions (plus configurable `brand_voice` / `quality_requirements`):

- Ground in supplied Knowledge Pack context; do not invent facts beyond it  
- Mark claims that still need verification  
- Avoid sensationalism and false certainty  
- Return only the required structured schema  

## Warnings

Job-level `warnings` may be attached on the generation when the executor records issues. The review UI surfaces `claims_requiring_verification` as **HUMAN CHECK REQUIRED**.
