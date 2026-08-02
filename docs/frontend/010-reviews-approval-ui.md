# Reviews & Approval UI

## Routes

| Route | Purpose |
|-------|---------|
| `/reviews` | Approval inbox with search, status filter, pagination |
| `/reviews/{approvalId}` | Review detail, snapshot sections, approve/reject/cancel |

## API

| Method | Endpoint | Usage |
|--------|----------|-------|
| GET | `/approvals` | Inbox list (`page`, `page_size`, `status`, `project_id`, `search`) |
| GET | `/approvals/{id}` | Detail + full snapshot + `version_approvals[]` |
| POST | `/approvals/{id}/approve` | Optional `{ comment }` |
| POST | `/approvals/{id}/reject` | Required `{ comment }` |
| POST | `/approvals/{id}/cancel` | Optional `{ comment }` (requester, pending only) |
| GET | `/content-versions/{versionId}/approvals` | History helper |

Hooks live in `src/lib/reviews/hooks.ts`: `useReviews`, `useApproval`, `useApproveApproval`, `useRejectApproval`, `useCancelApproval`.

## Snapshot display

Immutable version content uses plain-text sections separated by headers:

- `DISCOVERY BRIEF`
- `STORY SPINE`
- `MASTER SCRIPT`

`src/lib/scripts/snapshot.ts` → `parseSnapshot()` maps headers to document sections for read-only display on review and version pages.

## Review detail

- Parsed snapshot sections (read-only)
- Optional Knowledge Pack context when `script.knowledge_pack_id` is set
- Approve / Reject dialogs (reject requires comment)
- Cancel request when viewer is requester and status is `pending`
- Links to workspace and script version page

## Dashboard integration

`getDashboardData()` loads pending approvals via `GET /approvals?status=pending` (first page). Metric total uses response `total`. `403` → restricted empty state on Pending Reviews panel.

## Workspace integration

- **View Review** navigates to `/reviews/{pending_approval.id}` or `/reviews?status=pending`
- **Version history** uses script-scoped versions; **Open Version** → version page; **Open Review** when approval id matches pending/latest approval on that version
- **Revisions requested** banner loads rejection comment via `GET /approvals/{latest_approval.id}`
