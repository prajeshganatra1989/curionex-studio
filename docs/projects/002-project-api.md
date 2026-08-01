# Project API (M2E)

All endpoints require a valid JWT. Authorization uses permission codes.

## Projects

| Method | Path | Permission | Notes |
|--------|------|------------|-------|
| `POST` | `/projects` | `projects.create` | Creator becomes member; allocates `project_code` |
| `GET` | `/projects` | `projects.view` | Pagination + filters |
| `GET` | `/projects/{project_id}` | `projects.view` | Includes category + tags |
| `PATCH` | `/projects/{project_id}` | `projects.update` | Partial update; audits `changed_fields` |
| `DELETE` | `/projects/{project_id}` | `projects.delete` | Archives (`status=archived`) |

### List query parameters

| Param | Description |
|-------|-------------|
| `page` | Page number (≥ 1, default 1) |
| `page_size` | Page size (1–100, default 20) |
| `status` | `draft` \| `active` \| `archived` |
| `category_id` | UUID |
| `tag_id` | UUID |
| `created_by` | Creator user UUID |
| `search` | Case-insensitive match on `name` or `project_code` |

List response envelope: `{ items, page, page_size, total }`.

### Create body

```json
{
  "name": "Ancient Civilizations",
  "description": "Optional plain text",
  "status": "draft",
  "category_id": null,
  "tag_ids": []
}
```

## Members

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/projects/{project_id}/members` | `projects.view` |
| `POST` | `/projects/{project_id}/members/{user_id}` | `projects.update` |
| `DELETE` | `/projects/{project_id}/members/{user_id}` | `projects.update` |

Membership changes do not modify global roles. Duplicate membership returns `409`.

## Categories

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/categories` | `projects.view` |
| `POST` | `/categories` | `projects.create` |
| `PATCH` | `/categories/{category_id}` | `projects.update` |

Optional query: `active_only=true`.

## Tags

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/tags` | `projects.view` |
| `POST` | `/tags` | `projects.create` |
| `PATCH` | `/tags/{tag_id}` | `projects.update` |

## Errors

| Status | Meaning |
|--------|---------|
| `401` | Missing/invalid auth |
| `403` | Missing permission |
| `404` | Project / user / taxonomy not found |
| `409` | Duplicate slug or membership |
| `422` | Validation failure (status, slug, etc.) |
