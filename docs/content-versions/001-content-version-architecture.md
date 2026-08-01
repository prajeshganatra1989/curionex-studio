# Content Version Architecture (M2G)

ContentVersion is an **immutable snapshot** of content for a Project. Edits never mutate
an existing row — they create a new version.

## Relationship

```
Project 1──* ContentVersion 1──* Approval
```

Approvals belong to exactly one ContentVersion. They never attach to Project alone and
never transfer when a new version is created.

## Version numbering

- Sequential integer per project (`1`, `2`, `3`, …)
- Unique constraint: `(project_id, version_number)`
- Allocation uses `pg_advisory_xact_lock(project)` then `MAX(version_number)+1`
- Unique constraint is the safety net under races

Do **not** use unlocked `MAX()+1` alone.

## Lifecycle statuses

| Status | Meaning |
|--------|---------|
| `draft` | Editable workflow state (content still immutable) |
| `in_review` | Pending approval exists |
| `approved` | Approved for this exact version |
| `rejected` | Rejected; revise via a **new** version |
| `archived` | Retired version |

### Transitions

```
draft → in_review → approved
draft → in_review → rejected
in_review → draft   (approval cancelled)
```

Content/title never change across transitions.

## Latest / approved lookup

- Latest: highest `version_number` for the project
- Approved: highest `version_number` with `status=approved`

Use version numbers, not timestamps.

## Creator

`created_by` → `users.id`. No separate owner column.

## Authorization

1. Global permission: `content_versions.view` / `content_versions.create`
2. Project membership required for the version's project

Same pattern as Knowledge Packs.
