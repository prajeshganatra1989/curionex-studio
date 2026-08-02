# Version History UI

## Script-scoped versions

Version lists use script-scoped endpoints (not project title-prefix filtering):

| Method | Endpoint |
|--------|----------|
| GET | `/scripts/{scriptId}/content-versions` |
| GET | `/scripts/{scriptId}/content-versions/latest` |
| GET | `/scripts/{scriptId}/content-versions/approved` |
| GET | `/content-versions/{versionId}` |

`ContentVersion` rows include optional `script_id`.

## Version history panel

`VersionHistoryPanel` props:

- `projectId`, `scriptId`
- `workflow` — `WorkflowStatus` for Latest / Active / Approved badges
- `latestApproval` — from `GET /scripts/{id}/workflow` for Open Review on rejected rows

Actions per row:

- **Open Version** → `/projects/{projectId}/scripts/{scriptId}/versions/{versionId}`
- **Open Review** → `/reviews/{approvalId}` when pending or latest approval matches the version

## Script version page

Route: `/projects/{projectId}/scripts/{scriptId}/versions/{versionId}`

Read-only page parsing snapshot sections via `parseSnapshot()`. Validates `script_id` when present. Back link returns to workspace.

## Hooks

`useScriptVersions(scriptId)` replaces the former project list + `title.startsWith(scriptCode)` filter.

`useContentVersion(versionId)` loads a single version for the version page.
