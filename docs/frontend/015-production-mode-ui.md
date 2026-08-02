# Frontend — Production Mode UI

## Placement

Primary nav entry **Production** → `/production`. Complements the dashboard by focusing on the script journey and approved-script goal rather than mixed demo metrics.

## Surfaces

1. **Overview** — goals progress, stage count chips, AI job summary, quality rollups  
2. **Queue** — paginated, filterable list of scripts with derived stage + backend `next_action`  
3. **Metrics** — range selector (`today` / `7d` / `30d`)  
4. **Settings** — goal targets (visible to `production.view`; editable with `production.manage`)  
5. **Activity** — recent production audit events (restricted empty state without `audit.view`)

## Queue row contract

Each row shows:

- Project / script identity  
- Derived `production_stage` (never a client-invented status)  
- Document status indicators (complete / incomplete / missing) — **not** document bodies  
- Quality score/band when present  
- Primary CTA from `next_action.label` linking to `next_action.href`

Do not invent CTAs that bypass backend codes. Do not batch-generate or auto-advance scripts from this page.

## Filters

Support API filters the backend already exposes: `production_stage`, `search`, `project_id`, `blocked_only`, `pending_approval`, quality/AI filters, pagination, and sort (`priority` default).

## Permissions

| Action | Permission |
|--------|------------|
| View overview / queue / metrics / settings / activity | `production.view` |
| Patch goal targets | `production.manage` |

Reviewer can view Production Mode for membership-accessible projects but cannot edit settings.

## Copy principles

- Stages are **derived** — avoid copy that implies a separate “production status” field  
- AI actions remain advisory; human review remains the approval gate  
- Empty / restricted states should match other studio surfaces (no fake seed data)

## Related

- Backend: [../production/001-production-mode.md](../production/001-production-mode.md)
- Next actions: [../production/003-next-action-engine.md](../production/003-next-action-engine.md)
- Dashboard: [003-dashboard.md](003-dashboard.md)
