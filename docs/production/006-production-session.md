# Production Session

Guided daily workspace for Curionex Studio (`/production/session`).

## Purpose

Remove workflow friction. Users should open the session and continue the next logical production step — never hunt across Projects, Packs, Scripts, Versions, or Approvals.

## Session algorithm

`ProductionSessionService` (`app/services/production_session_service.py`) builds classified production units via the existing Production Mode classifier, then ranks **active** (non-approved) units.

### Selection buckets (ascending = higher priority)

1. **Blocked** — cannot proceed until resolved  
2. **Unfinished script** — discovery / spine / master / research / idea / needs revision  
3. **Waiting human review** — pending approval review  
4. **Needs AI generation** — queued/running AI or generate-* next action  
5. **Needs quality review**  
6. **Needs version** — ready for version / version created  
7. **Needs approval** — submit for human review  
8. **Completed** — excluded from current/queue  

### Tie-breakers

When multiple candidates share a bucket:

1. Lower **Wave** (Wave 1 first)  
2. Higher editorial **Priority** (A → B → C)  
3. **Oldest project** (`created_at` ascending)

The frontend must **not** reimplement this ordering.

## Continue engine

`continue_url` always comes from `resolve_next_action` deep links:

- Knowledge Pack pages  
- Script document workspace  
- Quality review detail  
- Version pages  
- Approval `/reviews/{id}`  

Never `/dashboard` or generic list hubs when a concrete work URL exists.

## Daily workflow

1. Open **Production Session**  
2. Read Today’s Goal + progress counter  
3. Press **Continue** on the current production  
4. Complete the step in the deep-linked surface  
5. Return — session refreshes and advances automatically when the current unit completes  

## API

`GET /production/session` — requires `production.view`

Returns today goals, progress counter, current production (timeline + sidebar), upcoming five, previous completed, warnings, empty-state browse URL.

## Streaks

`today.current_streak` is reserved. Until streak tracking ships, the API returns `0`.

## Related

- [001-production-mode.md](./001-production-mode.md)
- [002-production-stage-classification.md](./002-production-stage-classification.md)
- [003-next-action-engine.md](./003-next-action-engine.md)
- [004-production-goals.md](./004-production-goals.md)
