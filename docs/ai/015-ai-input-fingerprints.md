# AI Input Fingerprints

Snapshots of the inputs used for a Script Document draft, stored so editors can detect when upstream content changed after generation.

## Where stored

`input_fingerprint_json` on both:

- `ai_jobs` — captured at queue time  
- `ai_generations` — copied from the job when the generation is persisted  

API responses expose `input_fingerprint` and, when computable, `stale_input`.

## Snapshot shape

```json
{
  "document_type": "story_spine",
  "document_hashes": {
    "discovery_brief": "<sha256 hex>"
  },
  "knowledge_pack_id": "<uuid or null>",
  "knowledge_pack_section_hashes": {
    "research": "<sha256 hex>",
    "facts": "<sha256 hex>"
  },
  "settings_snapshot": {
    "brand_voice": "…",
    "quality_requirements": "…"
  }
}
```

`document_hashes` covers only **prerequisite** document types for the draft being generated (empty object for Discovery Brief). Section hashes cover every current Knowledge Pack section for the linked pack (empty if unlinked).

## Content hashes

`content_fingerprint(text)` = SHA-256 of UTF-8 bytes of `text.strip()` (empty string hashes the empty content).

Used for prerequisite document bodies and Knowledge Pack section bodies.

## Stale-input detection

`is_generation_stale` rebuilds the fingerprint from the script’s current documents, Knowledge Pack sections, and current brand voice / quality requirements, then compares to the stored snapshot (deep equality).

Returns `true` when any of those inputs differ. Apply still succeeds when stale; the response sets `stale_input: true` and the review UI warns the editor to consider regenerating.

Generation list/detail may include `stale_input`; listing never fails if a stale check errors.
