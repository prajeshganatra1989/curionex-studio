# Script Workspace API (M2H)

JWT required. Permission codes + project membership enforced.

## Project-scoped

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/projects/{project_id}/scripts` | `scripts.create` |
| `GET` | `/projects/{project_id}/scripts` | `scripts.view` |

### Create body

```json
{
  "title": "Episode Script",
  "description": "Optional",
  "knowledge_pack_id": null
}
```

Creates the script plus three empty document shells atomically.

### List query

| Param | Description |
|-------|-------------|
| `page` | ≥ 1 |
| `page_size` | 1–100 |
| `status` | Filter |
| `search` | Title or script_code |

List items omit nested documents.

## Script-scoped

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/scripts/{script_id}` | `scripts.view` |
| `PATCH` | `/scripts/{script_id}` | `scripts.update` |
| `DELETE` | `/scripts/{script_id}` | `scripts.delete` (archives) |
| `GET` | `/scripts/{script_id}/documents` | `scripts.view` |
| `GET` | `/scripts/{script_id}/documents/{document_type}` | `scripts.view` |
| `PATCH` | `/scripts/{script_id}/documents/{document_type}` | `scripts.update` |

Document types: `discovery_brief`, `story_spine`, `master_script`.

Document PATCH may update `title` and `content` only.
