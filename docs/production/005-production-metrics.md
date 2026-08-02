# Production Metrics

`GET /production/metrics?range=today|7d|30d` returns membership-scoped aggregates for the selected window.

## Fields

| Field | Meaning |
|-------|---------|
| `scripts_approved` | Distinct scripts with an approved Approval in range |
| `versions_created` | ContentVersions created in range |
| `quality_reviews_completed` | Quality-review generations with structured output in range |
| `average_quality_score` | Mean of `overall_score` from those reviews; `null` if none |
| `ai_jobs_completed` / `ai_jobs_failed` | Job terminal counts in range |
| `estimated_ai_cost` | Sum of `AiGeneration.cost_usd` in range |
| `average_days_to_approval` | Mean days from Script `created_at` to Approval `reviewed_at` |

## Overview AI / quality panels

Overview also exposes live AI job tallies (`queued` / `running` / `failed` / `completed_today`) and quality rollups (`average_current_score`, `scripts_needing_revision`, `stale_reviews`, `high_risk_fact_flags`) over current classified units — not a historical range.

## Activity

`GET /production/activity` lists recent production-relevant audit events when the caller has `audit.view`. Without it, the response is `{ items: [], restricted: true }`.

## Related

- [004-production-goals.md](004-production-goals.md)
- Audit catalog: [../audit/002-audit-event-catalog.md](../audit/002-audit-event-catalog.md)
