# Content Version API (M2G)

JWT required. Permission codes + project membership enforced.

## Project-scoped

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/projects/{project_id}/content-versions` | `content_versions.create` |
| `GET` | `/projects/{project_id}/content-versions` | `content_versions.view` |
| `GET` | `/projects/{project_id}/content-versions/latest` | `content_versions.view` |
| `GET` | `/projects/{project_id}/content-versions/approved` | `content_versions.view` |

### Create body

```json
{
  "title": "Discovery Brief v1",
  "content": "Immutable plain-text snapshot"
}
```

Creates `status=draft` with the next per-project version number.

### List query

| Param | Description |
|-------|-------------|
| `page` | ≥ 1 |
| `page_size` | 1–100 |
| `status` | Filter by lifecycle status |

Ordered by `version_number` descending.

## Version-scoped

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/content-versions/{version_id}` | `content_versions.view` |
| `POST` | `/content-versions/{version_id}/new-version` | `content_versions.create` |
| `POST` | `/content-versions/{version_id}/approval-requests` | `approvals.create` |
| `GET` | `/content-versions/{version_id}/approvals` | `approvals.view` |

There is **no** `PATCH /content-versions/{id}` for title/content.

### New version from existing

Copies title + content into a new draft at the next version number. Source row is unchanged and retains its approvals.
