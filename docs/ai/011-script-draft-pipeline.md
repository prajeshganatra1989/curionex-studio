# Script Draft Pipeline

Sequential AI drafting for Script Documents: Discovery Brief → Story Spine → Master Script.

Purpose codes:

| Purpose | Document type | Seeded prompt name |
|---------|---------------|--------------------|
| `script.discovery_brief.draft` | `discovery_brief` | Discovery Brief Draft |
| `script.story_spine.draft` | `story_spine` | Story Spine Draft |
| `script.master_script.draft` | `master_script` | Master Script Draft |

Generations are stored as `AiGeneration` rows. They are **never** written into `script_documents` until an editor explicitly applies them.

## Modes

**Step-by-step** — Generate from a single document editor (`Generate AI Draft`). Prerequisites are checked for that document only.

**Guided** — The workspace pipeline panel walks stages in order, surfaces blocked/ready/complete status, and suggests the next generate action. Still one draft job per stage; still human apply.

There is no unattended multi-stage run and no auto-apply between stages.

## Prerequisites

| Document | Requires non-empty |
|----------|--------------------|
| Discovery Brief | — (uses Knowledge Pack + project/script context when linked) |
| Story Spine | Discovery Brief |
| Master Script | Discovery Brief **and** Story Spine |

Missing or empty prerequisites return HTTP 422 with `missing` document types. See `GET …/ai-prerequisites`.

## Job lifecycle

`POST /scripts/{script_id}/documents/{document_type}/ai-drafts`

1. Resolve OpenAI model + active prompt version for the purpose  
2. Build input variables (project, Knowledge Pack sections, prior documents, brand voice, duration targets)  
3. Snapshot an **input fingerprint** on the job  
4. Queue `AiJob` (idempotency key unique per user + script + document type)  
5. Execute synchronously via `job_executor`  
6. Persist `AiGeneration` with structured output — **not** applied to the document

List drafts: `GET /scripts/{script_id}/ai-drafts` or `GET …/documents/{document_type}/ai-drafts`.

## Human review and apply

`POST /scripts/{script_id}/documents/{document_type}/ai-generations/{generation_id}/apply`

Conflict strategies:

| Strategy | Behavior |
|----------|----------|
| `reject_if_non_empty` (default) | 409 if the document already has content |
| `replace` | Overwrite document body with converted plain text |
| `append` | Append below existing content |

Apply updates only that document. It does **not** create a Content Version.

Apply response includes `stale_input` when upstream fingerprints no longer match (see [015-ai-input-fingerprints.md](015-ai-input-fingerprints.md)).

## Target documents

Only the three pipeline document types above. Other script document types have no draft purpose in this sprint.

## Related

- [012-discovery-brief-generation.md](012-discovery-brief-generation.md)
- [013-story-spine-generation.md](013-story-spine-generation.md)
- [014-master-script-generation.md](014-master-script-generation.md)
- [016-curionex-brand-voice.md](016-curionex-brand-voice.md)
