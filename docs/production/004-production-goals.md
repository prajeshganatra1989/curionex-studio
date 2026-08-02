# Production Goals

Goals live in `production_settings` (one expected row). They measure progress toward **approved scripts**, not drafts or AI completions.

## Defaults

| Field | Default | Max |
|-------|---------|-----|
| `approved_script_target` | 120 | 10000 |
| `daily_approved_script_target` | 2 | 100 |
| `weekly_approved_script_target` | 14 | 700 |

Created on first `GET` / `PATCH` via `get_or_create_settings`.

## Overview goal summary

| Field | Meaning |
|-------|---------|
| `approved_target` | Settings target |
| `approved_total` | Count of units currently in derived stage `approved` (membership-scoped) |
| `remaining` | `max(target - approved_total, 0)` |
| `completion_percent` | `(approved_total / target) * 100` |
| `approved_today` / `approved_this_week` | Distinct scripts with an approved Approval `reviewed_at` in range |
| `projected_days_remaining` | From recent daily approval rate when remaining > 0; else `null` |

Daily/weekly counters use Approval history; `approved_total` uses current derived stage so archived or reworked scripts do not inflate the goal indefinitely via old approvals alone.

## Mutation

`PATCH /production/settings` requires `production.manage`. Empty payloads and out-of-range values return 422. Successful changes write audit action `production.settings_updated` with old/new field metadata.

Reviewer role has `production.view` only — can read goals, cannot patch.

## Related

- [001-production-mode.md](001-production-mode.md)
- [005-production-metrics.md](005-production-metrics.md)
