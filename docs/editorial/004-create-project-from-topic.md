# Create Project from Topic

`POST /editorial-topics/{id}/create-project`

## Rules

1. Topic must not already have `linked_project_id`
2. Topic status must be `idea`, `planned`, or `in_progress`
3. Caller needs `editorial_topics.update` **and** `projects.create`
4. Creates a Project via `project_service.create_project` (membership for creator included)
5. Sets `linked_project_id` and status `project_created`
6. Does **not** create Knowledge Packs

## Request body

```json
{
  "name": "Optional override (defaults to topic title)",
  "description": "Optional",
  "category_id": null,
  "tag_ids": []
}
```

## Frontend

Topics table → **Create Project** opens a modal with name prefilled, category/tag pickers, then navigates to `/projects/{id}`.
