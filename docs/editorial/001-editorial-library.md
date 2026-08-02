# Editorial Library

The Editorial Library is the single source of truth for future YouTube Shorts ideas in Curionex Studio.

## Purpose

- Plan and organize evergreen topics (target capacity: 1,000+)
- Select what to produce next without AI generation in this sprint
- Create a Project from a topic when ready

## Data model

Table: `editorial_topics`

Key fields: `slug`, `title`, `category`, `status`, `difficulty`, scores, `linked_project_id`, `is_featured`.

Statuses: `idea` → `planned` → `in_progress` → `project_created` → `published` (or `archived`).

## Permissions

| Code | Meaning |
|------|---------|
| `editorial_topics.view` | List / detail / summary |
| `editorial_topics.create` | Create topics |
| `editorial_topics.update` | Update topics; create-project from topic |
| `editorial_topics.delete` | Soft-archive |

Create Project also requires `projects.create`.

## API

| Method | Path |
|--------|------|
| `GET` | `/editorial-topics` |
| `GET` | `/editorial-topics/summary` |
| `POST` | `/editorial-topics` |
| `GET` | `/editorial-topics/{id}` |
| `PATCH` | `/editorial-topics/{id}` |
| `DELETE` | `/editorial-topics/{id}` |
| `POST` | `/editorial-topics/{id}/create-project` |

## Frontend

- `/topics` — searchable, filterable, paginated library table
- Production Mode — Available / In Progress / Published counts + Browse Topics

## Related

- [002-topic-lifecycle.md](./002-topic-lifecycle.md)
- [003-topic-seeding.md](./003-topic-seeding.md)
- [004-create-project-from-topic.md](./004-create-project-from-topic.md)
- [005-editorial-audit.md](./005-editorial-audit.md)
