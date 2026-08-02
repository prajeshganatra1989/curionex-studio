# Dashboard

## Layout

1. Time-aware greeting with authenticated first name
2. Today’s Goal card (progress ring)
3. Metric cards (Projects, Knowledge Packs, Scripts, Drafts, Pending Reviews, Approved)
4. Recent Projects / Recent Scripts
5. Pending Reviews / Recent Activity

## Metrics & goal

Business target: **2 videos per day**.

Dashboard data loads through `src/lib/dashboard/data.ts` via `getDashboardData(api)`.

## Live vs mock (Sprint 2)

| Panel | Source | Indicator |
|-------|--------|-----------|
| Projects metric | Live — `GET /projects` `total` | No Demo badge |
| Recent Projects | Live — first page of `GET /projects` | Live |
| Pending Reviews metric + panel | Live — `GET /approvals?status=pending` | Live (403 → restricted empty state) |
| Knowledge Packs / Scripts / Drafts / Approved metrics | Demo adapter | Demo per card |
| Daily goal | Demo adapter | Demo |
| Recent Scripts | Demo adapter | Demo |
| Activity | Demo adapter | Demo |

Greeting shows **Mixed live + demo** while non-project modules remain mocked.

Components never hard-code demo numbers. Live project rows link to
`/projects/{id}`.

## Future

- Aggregation API for remaining metrics
- Publishing tracker for daily goal
- Audit feed (`audit.view`) for activity — restricted empty state when missing
