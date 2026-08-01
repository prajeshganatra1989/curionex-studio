# Script Workspace Architecture (M2H)

The Script Workspace is where project content-production documents are authored.

```
Project
 ├── Knowledge Packs          (research / context source of truth)
 └── Script Workspace
        ├── Discovery Brief
        ├── Story Spine
        └── Master Script
```

## Models

| Table | Purpose |
|-------|---------|
| `scripts` | Workspace container (code, title, status, optional KP + ContentVersion refs) |
| `script_documents` | Editable documents keyed by `document_type` |

Document bodies are **not** columns on `scripts`.

## Script code

Format: `{project_code}-S{NN}` (example `CRX-0001-S01`).

Allocation uses `pg_advisory_xact_lock(2, project_hash)` then scans existing codes for
the project. Unique `script_code` is the safety net.

## Knowledge Pack association

Optional `knowledge_pack_id`. Must belong to the **same** project. Content is never
copied — the pack remains the research source of truth.

## ContentVersion relationship

Optional `content_version_id` points at the canonical M2G `ContentVersion` layer.
M2H does **not** introduce `script_versions` or a second approval system.

Future flow:

```
Script documents → ContentVersion snapshot → Approval
```

## Lifecycle statuses

`draft` → `in_progress` → `in_review` → `approved` → `archived`

`DELETE` archives (`status=archived`). Documents are retained.

## Authorization

1. Global `scripts.view|create|update|delete`
2. Project membership for the script's project
