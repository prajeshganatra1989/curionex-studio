# Project Home

## Route

`/projects/[projectId]` — project control centre (Overview).

Additional tabs route to lightweight placeholders for later sprints:

- `/projects/[projectId]/packs`
- `/projects/[projectId]/scripts`
- `/projects/[projectId]/versions`
- `/projects/[projectId]/workflow`
- `/projects/[projectId]/activity`

Only Overview is fully implemented in Sprint 2.

## Overview sections

1. **Header** — CRX code, title, status, description, category, tags, updated
   time, Edit, Archive
2. **Knowledge Packs** — list total + latest packs (`GET .../knowledge-packs`)
3. **Scripts** — list total + latest scripts (`GET .../scripts`)
4. **Versions** — latest + approved (`.../content-versions/latest|approved`,
   404 → “Not available yet”)
5. **Workflow** — status for the most recent script
   (`GET /scripts/{id}/workflow/status`)
6. **Recent Activity** — unavailable state until project-scoped audit filtering
   ships (requires `audit.view`)

Counts use paginated list `total` fields — no full-table downloads.

## Quick actions

### Create Knowledge Pack

Modal → `POST /projects/{id}/knowledge-packs` (`name`, `description`, `status`).
Backend creates section shells. No section editor in this sprint.

### Create Script

Modal → `POST /projects/{id}/scripts` (`title`, `description`,
`knowledge_pack_id`). Knowledge Pack options are loaded from the same project
only. Backend creates document shells + workflow.

## Future editor navigation

Tabs and CTAs point at future editor routes/placeholders. Do not build the full
Knowledge Pack Editor or Script Workspace here.
