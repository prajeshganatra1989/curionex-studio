# Script-Scoped Content Versions

## Relationship

`ContentVersion.script_id` is a nullable UUID foreign key to `scripts.id`.

| Field | Purpose |
|-------|---------|
| `project_id` | Project ownership, membership, and per-project version numbering |
| `script_id` | Optional Script association for production workspace versions |

`ON DELETE SET NULL` preserves ContentVersion rows if a Script row is ever removed. Archiving a Script does not delete versions.

## Backward compatibility

- Existing / historical rows may have `script_id = NULL`
- Direct `POST /projects/{project_id}/content-versions` still allows project-only versions (`script_id` omitted)
- Optional `script_id` on create is accepted when the Script belongs to the **same** project
- Cross-project Script association is rejected with `422`
- No automatic title-prefix backfill was performed in the migration

## Workflow-created versions

`POST /scripts/{script_id}/workflow/create-version` always sets `script_id` to the current Script and verifies `Script.project_id == ContentVersion.project_id`.

`POST /content-versions/{id}/new-version` carries forward `script_id` (and `project_id`). The Script relationship cannot be changed after insert; ContentVersions remain immutable.

## Script-scoped queries

| Method | Path |
|--------|------|
| `GET` | `/scripts/{script_id}/content-versions` |
| `GET` | `/scripts/{script_id}/content-versions/latest` |
| `GET` | `/scripts/{script_id}/content-versions/approved` |

These query `ContentVersion.script_id` directly. They do **not** load all project versions and filter in memory.

## Forbidden association method

Associating versions by checking whether `title` begins with `{script_code} —` is forbidden.

Title prefixes may still appear as human-readable labels, but they are not a relational key.

## Approvals

Approvals remain tied only to `ContentVersion`. Script context is resolved through `ContentVersion.script_id`.

Inbox:

- `GET /approvals` (filters: `status`, `project_id`, `search`)
- `GET /approvals/{id}` returns an enriched detail payload including the immutable snapshot

## Migration

Revision: `d0a15c83e4f7`  
Revises: `c9g37d62b4f6`
