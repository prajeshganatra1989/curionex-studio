# Topic Lifecycle

| Status | Meaning |
|--------|---------|
| `idea` | Captured concept, not scheduled |
| `planned` | Selected for an upcoming production window |
| `in_progress` | Being researched / prepared before a project exists |
| `project_created` | Linked to a Curionex Project via `linked_project_id` |
| `published` | Short published (`published_video_url` may be set) |
| `archived` | Soft-removed from default browse |

## Transitions

- Manual status updates via `PATCH /editorial-topics/{id}`
- **Create Project** forces `idea|planned|in_progress` → `project_created` and sets `linked_project_id`
- Archive via `DELETE` (status = `archived` only)

Default list excludes archived topics unless `include_archived=true`.
