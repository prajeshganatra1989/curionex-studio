# Script Workflow UI

Backend remains authoritative. The frontend never invents stage transitions.

## Status display

`GET /scripts/{scriptId}/workflow/status` drives the workflow panel:

| Field | Meaning |
|-------|---------|
| `stage` | `workspace` · `versioning` · `review` · `completed` |
| `status` | Workflow status (`active`, `completed`, …) |
| `latest_version` | Newest project ContentVersion (context) |
| `active_version` | Version currently attached to the workflow |
| `approved_version` | Latest approved ContentVersion for the project |
| `pending_approval` | Pending Approval row for the active version |

**Latest**, **Active**, and **Approved** are always shown as separate rows.

`GET /scripts/{scriptId}/workflow` supplies `latest_approval` for rejected / revision banners after review returns to workspace.

## Create Version

- Endpoint: `POST /scripts/{scriptId}/workflow/create-version`
- Permission: `scripts.update`
- Allowed stages: `workspace`, `versioning`
- Frontend saves dirty documents first (or blocks on save failure)
- Confirmation dialog before call
- On success: invalidate script + workflow queries; toast version number

Does not edit immutable ContentVersion rows.

## Submit for Review

- Endpoint: `POST /scripts/{scriptId}/workflow/submit-review`
- Permission: `workflows.update`
- Requires stage `versioning` and an active version
- Frontend requires a clean (non-dirty) workspace
- Confirmation dialog; 409/422 surfaces as conflict/validation toasts

## Action button labels

Derived from stage + completion + latest approval:

| Condition | Label |
|-----------|-------|
| Incomplete workspace | Continue Writing |
| Ready workspace | Create Version |
| Versioning | Submit for Review |
| Review | View Review |
| Completed | Approved |
| Workspace + rejected approval | Revisions Requested |

Invalid actions are not offered as primary workflow CTA (Create Version header button still opens the confirm flow when the user chooses it).

## Approved / rejected

**Approved:** strong banner; approved version listed; workspace edits do not mutate the snapshot.

**Revisions requested:** banner after rejection return to workspace; loads reviewer comment from `GET /approvals/{latest_approval.id}`; user updates ScriptDocuments and must create a new version. Approval comments are not copied into documents.

## Review UI

Full approve / reject / cancel flows live at `/reviews` and `/reviews/{approvalId}`. See [010-reviews-approval-ui.md](./010-reviews-approval-ui.md).

- **View Review** opens the pending approval detail (or inbox when id unavailable)
- Version history **Open Review** uses the same routes
