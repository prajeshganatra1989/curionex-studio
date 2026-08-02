# Knowledge Pack Generation (v0.17.0)

## Purpose

Prompt purpose code: `knowledge_pack.draft`  
Seeded name: **Knowledge Pack Draft**

Variables: `topic`, `project_title`, `project_description`, `category`, `tags`, `target_audience`, `language`, `desired_depth`

## Structured schema

```json
{
  "research": "string",
  "facts": ["string"],
  "sources": [{"label":"string","reference":"string","verification_status":"unverified"}],
  "audience": "string",
  "content_angle": "string",
  "key_insights": ["string"],
  "additional_context": "string",
  "warnings": ["string"]
}
```

Every source is forced to `verification_status = "unverified"` on parse.

## Job lifecycle

`POST /projects/{project_id}/knowledge-packs/{knowledge_pack_id}/ai-drafts`

1. Resolve OpenAI model + active prompt version  
2. Queue `AiJob` with purpose, pack/project IDs, idempotency key  
3. Execute synchronously via `job_executor` (observable as job states)  
4. Persist `AiGeneration` with structured output — **not** written into the pack

## Human review and apply

`POST /knowledge-packs/{id}/ai-generations/{generation_id}/apply`

Conflict strategies:

| Strategy | Behavior |
|----------|----------|
| `reject_if_non_empty` (default) | 409 if selected sections have content |
| `replace_selected` | Replace selected section text |
| `append_selected` | Append below existing text |

Sources convert to plain text with `[UNVERIFIED — HUMAN CHECK REQUIRED]`.

## Idempotency

`idempotency_key` is unique per requesting user. Replays return the existing job and do not call the provider again.
