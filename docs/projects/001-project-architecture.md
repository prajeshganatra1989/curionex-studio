# Project Architecture (M2E)

Curionex Studio projects are the top-level container for future content production work
(knowledge packs, versions, approvals, attachments, automation). M2E implements only the
project foundation and taxonomy.

## Models

| Table | Purpose |
|-------|---------|
| `projects` | Project record (`project_code`, name, description, status, category, creator) |
| `project_members` | Participation join table (user ↔ project) |
| `categories` | Reusable taxonomy (unique slug, active flag) |
| `tags` | Reusable labels (unique normalized slug) |
| `project_tags` | Many-to-many project ↔ tag |

Primary keys are UUIDs. Descriptions are plain text (`TEXT`).

## Creator vs member

| Concept | Storage | Meaning |
|---------|---------|---------|
| Creator | `projects.created_by` → `users.id` | User who created the project; set once at creation |
| Member | `project_members` | User participates in the project |
| Owner column | **Not used** | No `owner_user_id`; avoid duplicating creator/membership |

On create, the authenticated creator is written to `created_by` **and** inserted into
`project_members` in the **same database transaction**.

Membership does **not** grant global RBAC roles. Global authorization remains
permission-code based (`projects.view`, `projects.create`, `projects.update`,
`projects.delete`).

## Lifecycle

Controlled statuses (application-enforced strings, not Postgres ENUMs):

- `draft` (default)
- `active`
- `archived`

`DELETE /projects/{id}` archives the project (`status = archived`). Rows are **not**
physically deleted so future content references remain stable. `project_code` never
changes after creation.

## Project code generation

Codes look like `CRX-0001`. Allocation uses PostgreSQL sequence `project_code_seq` via
`nextval` — never `SELECT MAX(project_code)`. Prefix and pad width are configurable
(`PROJECT_CODE_PREFIX`, `PROJECT_CODE_PAD_WIDTH`). See
[003-project-code-generation.md](003-project-code-generation.md).

## Permissions

| Permission | Used for |
|------------|----------|
| `projects.view` | List/detail projects, list members, list categories/tags |
| `projects.create` | Create projects, categories, tags |
| `projects.update` | Update projects/taxonomy; add/remove members |
| `projects.delete` | Archive projects |

These codes already exist in the RBAC seed catalog.

## Membership policy (M2E)

1. **Global permission** gates whether the caller may perform the API operation.
2. **Project membership** records participation; it is required conceptually for
   collaboration but does **not** bypass missing global permissions.
3. Callers without the relevant `projects.*` permission receive `403` even if they are
   members.
4. Adding/removing members never assigns or removes global roles.

### Knowledge Pack access (M2F+)

For Knowledge Packs, membership is **enforced** in addition to `knowledge_packs.*`
permissions: a caller with global permission but no membership on the pack's project
receives `403`. See `docs/knowledge-packs/001-knowledge-pack-architecture.md`.

## Categories and tags

- Categories: unique slug, optional description, `is_active`.
- Tags: unique normalized slug derived from name when omitted.
- A project may have zero or one category and many tags.
