# Project Home

## Route

`/projects/[projectId]` — project control centre (Overview).

Additional tabs:

- `/projects/[projectId]/packs` — Knowledge Pack list (opens editor)
- `/projects/[projectId]/scripts` — placeholder
- `/projects/[projectId]/versions` — placeholder
- `/projects/[projectId]/workflow` — placeholder
- `/projects/[projectId]/activity` — placeholder

Knowledge Pack Editor lives at
`/projects/[projectId]/knowledge-packs/[knowledgePackId]`
(see `007-knowledge-pack-editor.md`).

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
Backend creates section shells, then the UI navigates to the Knowledge Pack
Editor.

### Create Script

Modal → `POST /projects/{id}/scripts` (`title`, `description`,
`knowledge_pack_id`). Knowledge Pack options are loaded from the same project
only. Backend creates document shells + workflow.

## Editor navigation

Knowledge Pack rows open the research editor. Script Workspace remains a later
sprint.
