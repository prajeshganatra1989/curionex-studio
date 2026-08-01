# Workflow API

All endpoints are scoped to a Script and require project membership plus the listed permission.

Base path: `/scripts/{script_id}/workflow`

## GET `/scripts/{script_id}/workflow`

Permission: `workflows.view`

Returns workflow detail plus light related summaries:

- Script summary
- Knowledge pack id (via Script)
- Active ContentVersion summary (if any)
- Latest approval summary for the active version (if any)

Does not return full document or snapshot bodies.

## GET `/scripts/{script_id}/workflow/status`

Permission: `workflows.view`

Concise dashboard payload:

| Field | Meaning |
|-------|---------|
| `stage` | Current workflow stage |
| `status` | Current workflow status |
| `active_version` | Version currently associated with the workflow |
| `latest_version` | Highest version number in the project |
| `approved_version` | Latest approved version in the project |
| `pending_approval` | Pending approval for the active version, if any |

These three version concepts are intentionally distinct.

## POST `/scripts/{script_id}/workflow/transition`

Permission: `workflows.update`

Body:

```json
{ "target_stage": "versioning" }
```

Validates the transition map and preconditions. Invalid transitions return `422`.

## POST `/scripts/{script_id}/workflow/create-version`

Permission: `scripts.update`

Builds a deterministic plain-text snapshot from ScriptDocuments, creates a draft `ContentVersion`, sets `active_content_version_id`, and moves the workflow to `versioning`.

## POST `/scripts/{script_id}/workflow/submit-review`

Permission: `workflows.update`

Requires stage `versioning` and an active draft ContentVersion. Creates an Approval (M2G), sets version `in_review`, and moves workflow to `review`.

## POST `/scripts/{script_id}/workflow/archive`

Permission: `workflows.update`

Sets workflow `status = archived`. Retains all historical records.

## Approvals (unchanged M2G)

```
POST /approvals/{approval_id}/approve
POST /approvals/{approval_id}/reject
```

Permission: `approvals.review`

Workflow orchestration runs inside the existing approval service after a decision.
