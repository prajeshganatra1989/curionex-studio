# Dashboard

## Role vs Production Mode

| Surface | Job |
|---------|-----|
| **Dashboard** (`/dashboard`) | Live home snapshot after login |
| **Production** (`/production`) | Full pipeline queue, stages, filters, next actions |

Both use real backend data. Prefer fewer accurate cards over fake filler.

## Live sources

Dashboard data loads through `src/lib/dashboard/data.ts` via `getDashboardData(api)`.

| Item | Source | Notes |
|------|--------|-------|
| Projects metric + Recent Projects | `GET /projects` (`total` + first page) | Membership-scoped list total |
| Knowledge Packs / Scripts / Draft Scripts | `GET /production/overview` → `catalog` | Membership-scoped SQL counts |
| Approved Scripts / daily & weekly goals / remaining | `GET /production/overview` → `goals` | |
| Needs Revision / avg quality / stale reviews | `GET /production/overview` → `quality` | |
| AI running / failed | `GET /production/overview` → `ai` | |
| Pending Reviews metric | `GET /production/overview` → `stage_counts.pending_human_review` | |
| Pending Reviews list | `GET /approvals?status=pending` | Separate list permission |
| Recent Scripts | `GET /production/queue?sort=updated_at&page_size=5` | Script rows only |
| Recent Activity | `GET /production/activity` | `restricted: true` without `audit.view` |

## Availability policy

Each metric is one of:

- **live** — backend returned a value (including `0` or `null` for average quality)
- **unavailable** — request failed (network / 5xx); UI shows “Unavailable”, never a silent demo number
- **restricted** — `403` or activity `restricted: true`; UI shows “Restricted”

Failure is **never** coerced to `0`. Valid API zero is shown as `0`.

There is **no demo/mock Dashboard payload** in production code and no global “Demo data” badge.

## Refresh

The Dashboard **Refresh** control invalidates:

- `["dashboard"]`
- production overview + queue keys
- project list keys
- review list keys

then refetches the Dashboard query. Prior live data may remain visible while refreshing.

## Permissions

- `401` → existing auth flow
- Missing `production.view` → production-backed metrics/panels restricted or unavailable
- Missing approval list permission → pending list restricted (overview pending metric may still be live)
- Missing `audit.view` → activity restricted (empty items + flag)

## Related

- Production overview: [../production/001-production-mode.md](../production/001-production-mode.md)
- Production metrics: [../production/005-production-metrics.md](../production/005-production-metrics.md)
