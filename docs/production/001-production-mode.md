# Production Mode

Production Mode is an aggregation surface over existing Curionex Studio domains. It answers: **where is each script in the content journey, what should happen next, and how close are we to the approved-script goal?**

## What it is

| Concern | Source of truth |
|---------|-----------------|
| Content | Script Documents, Knowledge Packs, ContentVersions |
| Review decisions | Approvals |
| Lifecycle coordination | ContentWorkflow stage/status |
| **Derived production stage** | Computed at read time — not a stored column |
| Goals / targets | `production_settings` (singleton-style) |

Production Mode does **not** introduce a duplicate status field on Script or Project. Stages are derived from membership-scoped signals already owned by other modules.

## Endpoints

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/production/overview` | `production.view` |
| `GET` | `/production/queue` | `production.view` |
| `GET` | `/production/metrics` | `production.view` |
| `GET` | `/production/activity` | `production.view` |
| `GET` | `/production/settings` | `production.view` |
| `PATCH` | `/production/settings` | `production.manage` |

## Membership isolation

Queue, overview, and metrics only include projects where the caller is a `ProjectMember`. Reviewers with `production.view` see the same membership-scoped set; they cannot change goals without `production.manage`.

## Explicitly out of scope

- Batch AI generation or auto-advance through stages
- Auto-approval from quality scores
- Storing a parallel “production status” column
- Returning Script Document bodies in queue payloads (statuses only)

## Related

- [002-production-stage-classification.md](002-production-stage-classification.md)
- [003-next-action-engine.md](003-next-action-engine.md)
- [004-production-goals.md](004-production-goals.md)
- [005-production-metrics.md](005-production-metrics.md)
- Frontend: [../frontend/015-production-mode-ui.md](../frontend/015-production-mode-ui.md)
