# Dashboard

## Layout

1. Time-aware greeting with authenticated first name
2. Today’s Goal card (progress ring)
3. Metric cards (Projects, Knowledge Packs, Scripts, Drafts, Pending Reviews, Approved)
4. Recent Projects / Recent Scripts
5. Pending Reviews / Recent Activity

## Metrics & goal

Business target: **2 videos per day**.

Daily goal and metric counts currently come from an isolated demo adapter:

`src/lib/dashboard/data.ts`

A “Demo data” indicator marks non-live values. Components never hard-code demo
numbers.

## Live vs mock

| Panel | Sprint 1 source | Future |
|-------|-----------------|--------|
| Metrics | Mock adapter | Aggregation API |
| Daily goal | Mock adapter | Publishing tracker |
| Recent projects | Mock adapter | `GET /projects` summary |
| Recent scripts | Mock adapter | Scripts list API |
| Pending reviews | Mock adapter | Approvals inbox |
| Activity | Mock adapter | Audit feed (`audit.view`) |

If `audit.view` is missing later, show the restricted empty state — never a crash.
