# Content Version Immutability (M2G)

## Rule

Once a `ContentVersion` row is inserted, these fields never change:

- `title`
- `content`
- `version_number`
- `project_id`
- `created_by`
- `created_at`

`status` may change for lifecycle (`draft` → `in_review` → `approved` / `rejected`),
but the snapshot payload does not.

## Why

Historical reproducibility for scripts, voiceovers, and publishing later in the product
lifecycle. Future consumers must be able to resolve exactly what was approved.

## Enforcement

1. **API** — no update endpoint for immutable fields (`PATCH` returns 405)
2. **Service** — create-only for snapshots; new edits use `POST .../new-version`
3. **Database** — unique `(project_id, version_number)`; no update helpers for content

## Approvals do not transfer

```
Version 3 — approved  ✓
Version 4 — draft     (must request approval again)
```

Version 3's approval record remains forever on version 3.
