# Approvals (M2G)

Approvals are append-only records tied to **one** ContentVersion.

## Lifecycle

| Status | Meaning |
|--------|---------|
| `pending` | Awaiting review (at most one per version) |
| `approved` | Reviewer approved this version |
| `rejected` | Reviewer rejected this version |
| `cancelled` | Request withdrawn |

Partial unique index: one pending approval per `content_version_id`.

## Endpoints

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/content-versions/{id}/approval-requests` | `approvals.create` |
| `GET` | `/content-versions/{id}/approvals` | `approvals.view` |
| `GET` | `/approvals/{id}` | `approvals.view` |
| `POST` | `/approvals/{id}/approve` | `approvals.review` |
| `POST` | `/approvals/{id}/reject` | `approvals.review` |
| `POST` | `/approvals/{id}/cancel` | `approvals.create` |

## Version status coupling

| Action | Approval status | Version status |
|--------|-----------------|----------------|
| Request | pending | in_review |
| Approve | approved | approved |
| Reject | rejected | rejected |
| Cancel | cancelled | draft (if was in_review) |

## Re-approval rule

Approval of version N does **not** approve version N+1.

When a new version is created from an approved/rejected version:

- New version starts as `draft`
- New version has **no** approvals
- Historical approvals remain on the source version

## Reviewer fields

On approve/reject/cancel:

- `reviewed_by` set
- `reviewed_at` set
- optional `comment`
