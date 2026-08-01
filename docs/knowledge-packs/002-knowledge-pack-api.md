# Knowledge Pack API (M2F)

All endpoints require JWT auth. Authorization uses permission codes **and** project
membership for the related project.

## Project-scoped packs

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/projects/{project_id}/knowledge-packs` | `knowledge_packs.create` |
| `GET` | `/projects/{project_id}/knowledge-packs` | `knowledge_packs.view` |

### Create body

```json
{
  "name": "Ancient Rome Research",
  "description": "Optional plain text",
  "status": "draft"
}
```

Creates the pack plus seven empty section shells atomically.

### List query parameters

| Param | Description |
|-------|-------------|
| `page` | ≥ 1 (default 1) |
| `page_size` | 1–100 (default 20) |
| `status` | `draft` \| `active` \| `archived` |
| `search` | Case-insensitive name match |

Response: `{ items, page, page_size, total }` (list items omit nested sections).

## Pack-scoped

| Method | Path | Permission | Notes |
|--------|------|------------|-------|
| `GET` | `/knowledge-packs/{id}` | `knowledge_packs.view` | Includes ordered sections |
| `PATCH` | `/knowledge-packs/{id}` | `knowledge_packs.update` | name, description, status |
| `DELETE` | `/knowledge-packs/{id}` | `knowledge_packs.delete` | Archives (no hard delete) |

## Sections

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/knowledge-packs/{id}/sections` | `knowledge_packs.view` |
| `GET` | `/knowledge-packs/{id}/sections/{section_key}` | `knowledge_packs.view` |
| `PATCH` | `/knowledge-packs/{id}/sections/{section_key}` | `knowledge_packs.update` |
| `PATCH` | `/knowledge-packs/{id}/sections/reorder` | `knowledge_packs.update` |

Arbitrary section creation is not exposed in M2F.

### Section update body

```json
{
  "title": "Research",
  "content": "Plain text content"
}
```

### Reorder body

JSON array of all current section keys exactly once:

```json
[
  "research",
  "facts",
  "sources",
  "audience",
  "content_angle",
  "key_insights",
  "additional_context"
]
```

Invalid lists (duplicates, unknown keys, partial sets) return `422` with no partial update.

## Errors

| Status | Meaning |
|--------|---------|
| `401` | Unauthenticated |
| `403` | Missing permission or not a project member |
| `404` | Project / pack / section not found |
| `422` | Validation failure |
