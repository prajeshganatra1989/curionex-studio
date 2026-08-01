# Knowledge Pack Architecture (M2F)

A Knowledge Pack is the structured research and context layer for a Project. It is the
deterministic source-of-truth input for later content stages (Discovery Brief → Story
Spine → Master Script → Voiceover → Video). M2F does **not** generate AI content.

## Relationship to Project

- `knowledge_packs.project_id` → `projects.id`
- A project may have many Knowledge Packs
- Projects do **not** store a `knowledge_pack_id` column

## Models

| Table | Purpose |
|-------|---------|
| `knowledge_packs` | Pack metadata (name, description, status, creator, project) |
| `knowledge_pack_sections` | Extensible section rows (key, title, content, position) |

Sections are **rows**, never columns on `knowledge_packs`.

## Creator

`created_by` → `users.id`. There is no separate owner field. Authorization remains:

1. Global permission codes (`knowledge_packs.*`)
2. Project membership for the pack's project

## Lifecycle

Statuses (application-enforced):

- `draft` (default)
- `active`
- `archived`

`DELETE /knowledge-packs/{id}` sets `status=archived`. Pack and section rows are **not**
physically deleted so future content versions can keep stable references.

## Section architecture

On create, seven empty section shells are inserted from the central catalog in the same
transaction as the pack. Ordering uses integer `position` (ASC), with `section_key` as a
stable secondary sort.

Uniqueness: `(knowledge_pack_id, section_key)`.

See [003-section-catalog.md](003-section-catalog.md).

## Authorization policy

| Layer | Role |
|-------|------|
| Global RBAC | `require_permission("knowledge_packs.view\|create\|update\|delete")` |
| Project access | Caller must be a **project member** of the pack's project |

Having a global permission alone is insufficient to read/mutate another project's packs.
Membership alone is insufficient without the matching permission code.

## Future AI

Automation may later populate section content. M2F stays manually editable and
provider-agnostic. See [004-future-ai-integration.md](004-future-ai-integration.md).
