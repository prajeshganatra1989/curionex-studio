# Curionex Studio — Database Architecture (v0.1)

Status: **Architecture only** — no migrations, models, or PostgreSQL connection in this document.

Technology: **PostgreSQL** (ORM later: SQLAlchemy; migrations later: Alembic)

---

## 1. Database goals

1. Support the v0.1 content workflow: Idea → Research → Discovery Brief → Story Spine → Master Script → Production Guide → Publishing.
2. Provide a durable foundation for multi-user collaboration: authentication, RBAC, assignment, comments, approvals, version history, and audit logging.
3. Keep the schema normalized, UUID-keyed, and evolvable toward future AI, automation (n8n / Studio Engine), publishing, analytics, and optional multi-tenant workspaces — without implementing those features now.
4. Prefer clear relational structures over premature polymorphism and overuse of JSON.

---

## 2. Design principles

| Principle | Meaning |
|-----------|---------|
| UUID primary keys | Application entities use `UUID` PKs (`gen_random_uuid()`). |
| Soft delete where recoverable | Business records that users may restore use `deleted_at`. |
| Append-only history | Audit logs, content versions, and approval records are never overwritten. |
| Configurable RBAC | Roles and permissions live in tables; application code checks permission codes, not role names. |
| Sections as rows | Knowledge Pack sections are entities, not project columns. |
| Explicit ownership vs assignment | Project owner, creator, and assignees are separate concepts. |
| Secure by default | Password hashes only; never store secrets in settings or audit payloads. |
| MVP discipline | Fields/tables marked **MVP REQUIRED** vs **FUTURE / OPTIONAL**. |
| JSONB sparingly | Use for audit metadata / flexible settings values — not as a substitute for relationships. |

---

## 3. Entity list

### MVP REQUIRED

| Entity | Table | Purpose |
|--------|-------|---------|
| User | `users` | Accounts and authentication credentials |
| Role | `roles` | Named, configurable roles |
| Permission | `permissions` | Granular permission codes |
| Role ↔ Permission | `role_permissions` | Many-to-many |
| User ↔ Role | `user_roles` | Many-to-many |
| Category | `categories` | Single category per project |
| Tag | `tags` | Reusable labels |
| Project | `projects` | Content asset (e.g. CRX-0001) |
| Project ↔ Tag | `project_tags` | Many-to-many |
| Project member | `project_members` | Assignees (separate from owner) |
| Knowledge pack | `knowledge_packs` | 1:1 container under a project |
| Knowledge pack section | `knowledge_pack_sections` | Discovery Brief, Story Spine, etc. |
| Content version | `content_versions` | Immutable version snapshots |
| Comment | `comments` | Feedback on a project section |
| Approval | `approvals` | Append-only approval workflow history |
| Audit log | `audit_logs` | Append-only system activity |
| Attachment | `attachments` | File metadata only |
| System setting | `system_settings` | Non-secret application configuration |
| User preference | `user_preferences` | Per-user UI/workflow preferences |

### FUTURE / OPTIONAL (documented, not required for v0.1 implementation)

| Entity | Notes |
|--------|-------|
| `workspaces` / `workspace_members` | Multi-tenant SaaS boundary |
| `refresh_tokens` / `sessions` | Token persistence beyond JWT if needed |
| `password_reset_tokens` / `email_verification_tokens` | Or equivalent secure token stores |
| `automation_jobs` | n8n / Studio Engine job tracking |
| `ai_generation_runs` | AI/ElevenLabs/image/video run history |
| `publishing_targets` / `analytics_snapshots` | YouTube and analytics |

---

## 4–9. Detailed table definitions

Conventions used below:

- Timestamps: `TIMESTAMPTZ`, stored in UTC.
- Soft delete: nullable `deleted_at TIMESTAMPTZ` — row is soft-deleted when non-null.
- Actor FKs: `ON DELETE SET NULL` or `RESTRICT` as noted; prefer retaining history over cascading deletes of users.
- Status / type fields: `VARCHAR` with application-enforced allowed values (easier to evolve than Postgres ENUMs for v0.1).

---

### 4.1 `users` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `email` | `CITEXT` or `VARCHAR(320)` | NO | | Unique among non-deleted rows |
| `full_name` | `VARCHAR(255)` | NO | | Display name |
| `password_hash` | `VARCHAR(255)` | NO | | Argon2/bcrypt hash only |
| `is_active` | `BOOLEAN` | NO | `TRUE` | Inactive users cannot authenticate |
| `last_login_at` | `TIMESTAMPTZ` | YES | | Updated on successful login |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete |

**FUTURE / OPTIONAL columns (do not require in first migration):**

| Column | Type | Notes |
|--------|------|-------|
| `email_verified_at` | `TIMESTAMPTZ` | Email verification |
| `password_reset_token_hash` | `VARCHAR(255)` | Prefer separate token table instead |
| `password_reset_expires_at` | `TIMESTAMPTZ` | Prefer separate token table instead |
| `avatar_url` | `VARCHAR(1024)` | Profile image |
| `workspace_id` | `UUID` | Multi-tenancy evolution |

**Constraints / indexes**

- PK: `id`
- Unique: `(email)` where `deleted_at IS NULL` (partial unique index)
- Index: `(is_active)`, `(deleted_at)`, `(last_login_at)`

**Security:** never store plaintext passwords, reset tokens in plaintext, or API keys on this table.

---

### 4.2 `roles` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `code` | `VARCHAR(64)` | NO | | Stable machine code, e.g. `admin` |
| `name` | `VARCHAR(128)` | NO | | Human label, e.g. `Admin` |
| `description` | `TEXT` | YES | | |
| `is_system` | `BOOLEAN` | NO | `FALSE` | Protect seeded roles from deletion |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete / deactivate |

Example seed roles (data, not schema): Super Admin, Admin, Researcher, Script Writer, Reviewer, Viewer.

**Constraints / indexes:** unique `(code)` where `deleted_at IS NULL`.

---

### 4.3 `permissions` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `code` | `VARCHAR(64)` | NO | | e.g. `SCRIPT_APPROVE` |
| `name` | `VARCHAR(128)` | NO | | |
| `description` | `TEXT` | YES | | |
| `resource` | `VARCHAR(64)` | NO | | e.g. `user`, `project`, `script` |
| `action` | `VARCHAR(64)` | NO | | e.g. `view`, `create`, `approve` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |

Permissions are immutable catalogs in practice; soft delete is optional. Prefer deactivating via not assigning them.

**MVP permission codes (seed data):**

`USER_VIEW`, `USER_CREATE`, `USER_UPDATE`, `USER_DELETE`,  
`PROJECT_VIEW`, `PROJECT_CREATE`, `PROJECT_UPDATE`, `PROJECT_DELETE`,  
`SCRIPT_VIEW`, `SCRIPT_CREATE`, `SCRIPT_UPDATE`, `SCRIPT_APPROVE`, `SCRIPT_LOCK`,  
`AUDIT_LOG_VIEW`

**Constraints / indexes:** unique `(code)`; index `(resource, action)`.

---

### 4.4 `role_permissions` — MVP REQUIRED

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `role_id` | `UUID` | NO | FK → `roles.id` `ON DELETE CASCADE` |
| `permission_id` | `UUID` | NO | FK → `permissions.id` `ON DELETE CASCADE` |
| `created_at` | `TIMESTAMPTZ` | NO | |

**PK:** `(role_id, permission_id)`

---

### 4.5 `user_roles` — MVP REQUIRED

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `user_id` | `UUID` | NO | FK → `users.id` `ON DELETE CASCADE` |
| `role_id` | `UUID` | NO | FK → `roles.id` `ON DELETE RESTRICT` |
| `assigned_at` | `TIMESTAMPTZ` | NO | |
| `assigned_by_id` | `UUID` | YES | FK → `users.id` `ON DELETE SET NULL` |

**PK:** `(user_id, role_id)`  
**Index:** `(role_id)`

---

### 4.6 `categories` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `name` | `VARCHAR(128)` | NO | | |
| `slug` | `VARCHAR(128)` | NO | | URL/stable key |
| `description` | `TEXT` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete |

**Unique:** `(slug)` where `deleted_at IS NULL`

---

### 4.7 `tags` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `name` | `VARCHAR(64)` | NO | | |
| `slug` | `VARCHAR(64)` | NO | | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | |

**Unique:** `(slug)` where `deleted_at IS NULL`

---

### 4.8 `projects` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `crx_id` | `VARCHAR(32)` | NO | | e.g. `CRX-0001` |
| `title` | `VARCHAR(500)` | NO | | |
| `description` | `TEXT` | YES | | |
| `season` | `INTEGER` | YES | | |
| `episode` | `INTEGER` | YES | | |
| `category_id` | `UUID` | YES | | FK → `categories.id` `ON DELETE SET NULL` |
| `status` | `VARCHAR(32)` | NO | `'idea'` | Workflow status |
| `priority` | `VARCHAR(16)` | NO | `'medium'` | `low` / `medium` / `high` |
| `owner_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` — accountable owner |
| `created_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` — immutable creator |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete |

**MVP status values (application-enforced):**  
`idea`, `research`, `in_progress`, `in_review`, `changes_requested`, `approved`, `locked`, `published`, `archived`

**Constraints / indexes**

- Unique: `(crx_id)` where `deleted_at IS NULL`
- Indexes: `(status)`, `(owner_id)`, `(category_id)`, `(created_by_id)`, `(deleted_at)`, `(season, episode)`

**Ownership model**

| Concept | Field / table | Meaning |
|---------|---------------|---------|
| Creator | `created_by_id` | Who created the project (historical) |
| Owner | `owner_id` | Who is accountable; may change |
| Assignees | `project_members` | Collaborators with optional project-local role label |

---

### 4.9 `project_tags` — MVP REQUIRED

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `project_id` | `UUID` | NO | FK → `projects.id` `ON DELETE CASCADE` |
| `tag_id` | `UUID` | NO | FK → `tags.id` `ON DELETE CASCADE` |
| `created_at` | `TIMESTAMPTZ` | NO | |

**PK:** `(project_id, tag_id)`

---

### 4.10 `project_members` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `project_id` | `UUID` | NO | | FK → `projects.id` `ON DELETE CASCADE` |
| `user_id` | `UUID` | NO | | FK → `users.id` `ON DELETE CASCADE` |
| `assignment_role` | `VARCHAR(64)` | YES | | Optional label, e.g. `researcher` (not RBAC) |
| `assigned_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `assigned_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |

**Unique:** `(project_id, user_id)`  
**Index:** `(user_id)`

`assignment_role` is a project collaboration hint. Authorization still comes from global RBAC permissions.

---

### 4.11 `knowledge_packs` — MVP REQUIRED

One Knowledge Pack per project (container for sections).

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `project_id` | `UUID` | NO | | FK → `projects.id` `ON DELETE CASCADE` |
| `status` | `VARCHAR(32)` | NO | `'draft'` | Pack-level rollup status (optional UX) |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete with project |

**Unique:** `(project_id)` — enforces 1:1

---

### 4.12 `knowledge_pack_sections` — MVP REQUIRED

Sections are **rows**, not columns on `projects`.

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `knowledge_pack_id` | `UUID` | NO | | FK → `knowledge_packs.id` `ON DELETE CASCADE` |
| `section_type` | `VARCHAR(64)` | NO | | See allowed values |
| `status` | `VARCHAR(32)` | NO | `'draft'` | Section workflow status |
| `current_version_id` | `UUID` | YES | | FK → `content_versions.id` `ON DELETE SET NULL` |
| `created_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `updated_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete |

**MVP `section_type` values:**  
`discovery_brief`, `story_spine`, `master_script`, `production_guide`, `publishing`

**MVP `status` values:**  
`draft`, `in_review`, `changes_requested`, `approved`, `locked`

**Unique:** `(knowledge_pack_id, section_type)` where `deleted_at IS NULL`  
**Index:** `(status)`, `(current_version_id)`

**Note on circular FK:** `current_version_id` → `content_versions` while versions point back to the section. Create `content_versions` first without the reverse FK, then add `current_version_id`, **or** defer the FK constraint. Documented in decisions.

Live body content lives on the **current version**, not duplicated as a free-floating column (optional denormalized `title` cache is FUTURE only).

---

### 4.13 `content_versions` — MVP REQUIRED

Immutable snapshots. Generic via `entity_type` + `entity_id` so other content types can reuse the table later.

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `entity_type` | `VARCHAR(64)` | NO | | MVP: `knowledge_pack_section` |
| `entity_id` | `UUID` | NO | | MVP: section id (logical FK) |
| `version_label` | `VARCHAR(32)` | NO | | e.g. `v1.0`, `v1.1`, `v2.0` |
| `version_major` | `INTEGER` | NO | | For ordering |
| `version_minor` | `INTEGER` | NO | | For ordering |
| `content` | `TEXT` | NO | | Full snapshot body |
| `change_summary` | `TEXT` | YES | | What changed |
| `previous_version_id` | `UUID` | YES | | FK → `content_versions.id` `ON DELETE SET NULL` |
| `is_current` | `BOOLEAN` | NO | `FALSE` | Exactly one current per entity (app-enforced) |
| `created_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | No `updated_at` — immutable |

**No soft delete.** Versions are historical facts. Mistakes are corrected by a new version.

**Constraints / indexes**

- Unique: `(entity_type, entity_id, version_major, version_minor)`
- Unique partial: one `is_current = TRUE` per `(entity_type, entity_id)` (partial unique index)
- Index: `(entity_type, entity_id, created_at DESC)`
- Index: `(previous_version_id)`

**Integrity note:** `entity_id` is intentionally **not** a hard FK to multiple tables. Application services validate that the entity exists. This avoids fragile polymorphic FKs while remaining queryable.

---

### 4.14 `comments` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `project_id` | `UUID` | NO | | FK → `projects.id` `ON DELETE CASCADE` |
| `section_id` | `UUID` | YES | | FK → `knowledge_pack_sections.id` `ON DELETE SET NULL` |
| `author_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `body` | `TEXT` | NO | | |
| `parent_comment_id` | `UUID` | YES | | FK → `comments.id` `ON DELETE SET NULL` — FUTURE threads; nullable in MVP |
| `is_resolved` | `BOOLEAN` | NO | `FALSE` | |
| `resolved_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `resolved_at` | `TIMESTAMPTZ` | YES | | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete |

**Indexes:** `(project_id, created_at DESC)`, `(section_id)`, `(author_id)`, `(is_resolved)`, `(parent_comment_id)`

MVP UI may ignore threading; column is reserved so a later migration is unnecessary.

---

### 4.15 `approvals` — MVP REQUIRED

Append-only approval history. A new decision creates a **new row**; prior rows remain.

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `project_id` | `UUID` | NO | | FK → `projects.id` `ON DELETE CASCADE` |
| `section_id` | `UUID` | NO | | FK → `knowledge_pack_sections.id` `ON DELETE CASCADE` |
| `content_version_id` | `UUID` | NO | | FK → `content_versions.id` `ON DELETE RESTRICT` — version under review |
| `status` | `VARCHAR(32)` | NO | | See values |
| `submitted_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `reviewer_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `decision_reason` | `TEXT` | YES | | Comments / reason |
| `submitted_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `decided_at` | `TIMESTAMPTZ` | YES | | When review completed |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |

**No soft delete / no updates to status in place.** Corrections = new approval row. Optional: allow updating only `reviewer_id` / `decided_at` on an open `in_review` row; prefer append-only for decisions.

**MVP status values:**  
`draft_submission`, `in_review`, `changes_requested`, `approved`, `locked`

**Indexes:** `(section_id, created_at DESC)`, `(content_version_id)`, `(status)`, `(reviewer_id)`, `(project_id)`

---

### 4.16 `audit_logs` — MVP REQUIRED (CORE)

Append-only. Never soft-deleted. Never updated.

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `actor_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` — null for system/anonymous |
| `action` | `VARCHAR(64)` | NO | | e.g. `PROJECT_CREATED` |
| `entity_type` | `VARCHAR(64)` | NO | | e.g. `project`, `user` |
| `entity_id` | `UUID` | YES | | Logical reference; no polymorphic FK |
| `ip_address` | `INET` | YES | | Optional request context |
| `user_agent` | `VARCHAR(512)` | YES | | Optional; truncate |
| `metadata` | `JSONB` | YES | | Non-sensitive context |
| `old_values` | `JSONB` | YES | | Redacted before write |
| `new_values` | `JSONB` | YES | | Redacted before write |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | Event time |

**No `updated_at`, no `deleted_at`.**

**Indexes:** `(created_at DESC)`, `(actor_id, created_at DESC)`, `(entity_type, entity_id, created_at DESC)`, `(action, created_at DESC)`

**MVP action examples:**  
`USER_CREATED`, `USER_UPDATED`, `USER_DEACTIVATED`,  
`PROJECT_CREATED`, `PROJECT_UPDATED`, `PROJECT_DELETED`,  
`SCRIPT_CREATED`, `SCRIPT_UPDATED`, `SCRIPT_APPROVED`, `SCRIPT_LOCKED`,  
`COMMENT_CREATED`, `COMMENT_RESOLVED`,  
`LOGIN_SUCCESS`, `LOGIN_FAILED`

**Redaction rules:** never persist passwords, password hashes, tokens, API keys, or secrets in `metadata` / `old_values` / `new_values`.

---

### 4.17 `attachments` — MVP REQUIRED (metadata only)

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `project_id` | `UUID` | NO | | FK → `projects.id` `ON DELETE CASCADE` |
| `section_id` | `UUID` | YES | | FK → `knowledge_pack_sections.id` `ON DELETE SET NULL` |
| `uploaded_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `file_name` | `VARCHAR(512)` | NO | | Original name |
| `content_type` | `VARCHAR(255)` | NO | | MIME type |
| `byte_size` | `BIGINT` | NO | | |
| `storage_key` | `VARCHAR(1024)` | NO | | Object-store / filesystem key (not binary) |
| `checksum_sha256` | `CHAR(64)` | YES | | Integrity |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `deleted_at` | `TIMESTAMPTZ` | YES | | Soft delete metadata; file GC later |

**Indexes:** `(project_id)`, `(section_id)`, `(storage_key)` unique

Do **not** store file bytes in PostgreSQL for v0.1.

---

### 4.18 `system_settings` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `key` | `VARCHAR(128)` | NO | | e.g. `ui.default_project_status` |
| `value` | `JSONB` | NO | | Non-secret config |
| `description` | `TEXT` | YES | | |
| `updated_by_id` | `UUID` | YES | | FK → `users.id` `ON DELETE SET NULL` |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |

**Unique:** `(key)`

**Forbidden:** API keys, OAuth secrets, DB passwords, ElevenLabs/OpenAI tokens. Those belong in environment / secret manager.

---

### 4.19 `user_preferences` — MVP REQUIRED

| Column | Type | Null | Default | Notes |
|--------|------|------|---------|-------|
| `id` | `UUID` | NO | `gen_random_uuid()` | PK |
| `user_id` | `UUID` | NO | | FK → `users.id` `ON DELETE CASCADE` |
| `key` | `VARCHAR(128)` | NO | | e.g. `ui.theme` |
| `value` | `JSONB` | NO | | |
| `created_at` | `TIMESTAMPTZ` | NO | `now()` | |
| `updated_at` | `TIMESTAMPTZ` | NO | `now()` | |

**Unique:** `(user_id, key)`

---

## 10. Relationships (summary)

```
users ──┬──< user_roles >── roles ──< role_permissions >── permissions
        ├──< project_members >── projects
        ├── owns projects (owner_id)
        └── creates projects (created_by_id)

categories ──< projects
tags ──< project_tags >── projects

projects ──1:1── knowledge_packs ──1:N── knowledge_pack_sections
knowledge_pack_sections ──1:N── content_versions
knowledge_pack_sections ──0:1── current content_versions (current_version_id)

projects / sections ──1:N── comments
projects / sections / versions ──1:N── approvals
projects / sections ──1:N── attachments

users ──?── audit_logs (actor_id, logical entity refs)
users ──1:N── user_preferences
system_settings (standalone)
```

See [002-entity-relationship.md](./002-entity-relationship.md) for the Mermaid ER diagram.

---

## 11. Soft deletion strategy

| Soft-deleted (`deleted_at`) | Never soft-deleted | Hard rules |
|-----------------------------|--------------------|------------|
| `users`, `roles`, `categories`, `tags` | `audit_logs` | Audit is append-only forever |
| `projects`, `knowledge_packs`, `knowledge_pack_sections` | `content_versions` | Versions are immutable history |
| `comments`, `attachments` | `approvals` (decision rows) | Prefer append-only decisions |
| | `permissions`, join tables | Cascade/remove associations |

Queries for user-facing lists **must** filter `deleted_at IS NULL` unless explicitly viewing trash/admin restore.

Deactivating a user: set `is_active = FALSE` **and/or** soft-delete; prefer `is_active` for login denial without losing FK visibility.

---

## 12. Versioning strategy

1. Editing a section creates a **new** `content_versions` row (full content snapshot).
2. Set `previous_version_id` to the prior current version.
3. Flip `is_current` (transactionally) and update `knowledge_pack_sections.current_version_id`.
4. `version_label` / `version_major` / `version_minor` support human labels (`v1.2`) and ordering.
5. Approvals always reference a specific `content_version_id`.
6. Answering “who / when / what changed / previous / current / approved” is done via version rows + approval rows — never by overwriting `content`.

Generic `entity_type` / `entity_id` allows future versioning of non-section artifacts without a second versioning subsystem.

---

## 13. Approval strategy

Workflow (section-level, version-scoped):

`draft` → `in_review` → `changes_requested` → `approved` → `locked`

| Concern | Approach |
|---------|----------|
| History | Each submission/decision is a row in `approvals` |
| Version coupling | `content_version_id` is required |
| Who submitted / reviewed | `submitted_by_id`, `reviewer_id` |
| Reason | `decision_reason` |
| Locking | Section `status = locked` + permission `SCRIPT_LOCK`; locked sections reject content edits |

Approved version ≠ automatically current version if further edits create `v1.3` after approval of `v1.2`; product rules should define whether approval clears on new versions (recommended: new version resets section to `draft` / requires re-approval).

---

## 14. RBAC strategy

1. Seed `permissions` with stable codes (`SCRIPT_APPROVE`, etc.).
2. Seed default `roles`; mark `is_system = TRUE` for built-ins.
3. Attach permissions via `role_permissions` only — **never** hard-code role names in authorization checks.
4. Assign users via `user_roles` (users may hold multiple roles; effective permissions = union).
5. Custom roles = new `roles` rows + permission links.
6. Project `assignment_role` does **not** grant permissions; it is organizational metadata.

Optional FUTURE: resource-scoped permissions (per-project ACLs). Not in v0.1 schema.

---

## 15. Audit logging strategy

1. Write audit rows in the same transaction as the business change when possible.
2. Use stable `action` codes.
3. Reference targets with `entity_type` + `entity_id` (no polymorphic FK).
4. Store redacted `old_values` / `new_values` as JSONB.
5. Application must treat the table as append-only (no UPDATE/DELETE APIs).
6. `LOGIN_FAILED` may have `actor_id = NULL` and email in redacted metadata (not password).

---

## 16. Security considerations

- Password hashing only (Argon2id or bcrypt); never reversible encryption for passwords.
- Audit/settings must not contain secrets.
- Attachment table stores paths/keys only; authorize downloads in the API layer.
- Soft-deleted users remain referenced historically (`SET NULL` vs retaining id — prefer retaining `actor_id` with `SET NULL` only if user hard-removed; soft-delete keeps the row).
- Prefer partial unique indexes so soft-deleted emails/CRX IDs can be recycled intentionally — product decision required.
- Rate-limit and lockout for auth are application concerns, not schema.

---

## 17. MVP vs future fields

### MVP REQUIRED

- Full RBAC tables + seedable roles/permissions  
- Projects, members, category, tags  
- Knowledge pack + sections  
- Content versions + approvals + comments  
- Audit logs + attachment metadata  
- System settings + user preferences (non-secret)

### FUTURE / OPTIONAL

| Area | Evolution |
|------|-----------|
| Auth extras | Email verification, reset token tables, refresh sessions |
| Multi-tenancy | `workspaces`, `workspace_id` on users/projects |
| Automation | `automation_jobs` (`provider`, `external_id`, `status`, `payload` JSONB, `project_id`) for n8n without redesigning projects |
| AI / media | Generation run tables linked to section/version |
| Publishing | External platform IDs, publish receipts |
| Comments | Full threaded UX using existing `parent_comment_id` |
| Search | Full-text indexes on `content_versions.content` / project titles |

---

## Index recommendation checklist

| Table | Key indexes |
|-------|-------------|
| `users` | unique email (partial), `is_active`, `deleted_at` |
| `permissions` | unique `code`, `(resource, action)` |
| `projects` | unique `crx_id` (partial), `status`, `owner_id`, `category_id` |
| `project_members` | unique `(project_id, user_id)`, `user_id` |
| `knowledge_pack_sections` | unique `(pack, section_type)` partial, `status` |
| `content_versions` | unique version tuple, current partial unique, entity timeline |
| `comments` | project timeline, section, resolved |
| `approvals` | section timeline, version, status |
| `audit_logs` | time, actor+time, entity+time, action+time |
| `attachments` | unique `storage_key`, project/section |

---

## Architectural questions — answers

| # | Question | Decision |
|---|----------|----------|
| 1 | Ownership vs assignment separate? | **Yes.** `owner_id`, `created_by_id`, `project_members`. |
| 2 | Sections as entities? | **Yes.** `knowledge_pack_sections` rows with `section_type`. |
| 3 | Generic version history? | **`content_versions`** with `entity_type`/`entity_id`, immutable snapshots. |
| 4 | Approvals ↔ versions? | Approvals **require** `content_version_id`; history is append-only. |
| 5 | Audit ↔ entities? | Logical `entity_type` + `entity_id`; no polymorphic FK. |
| 6 | Soft delete which? | Business entities (users, projects, sections, comments, attachments, taxonomy). |
| 7 | Never delete? | `audit_logs`, `content_versions`, approval decision history. |
| 8 | JSONB where? | Audit payloads, settings/preferences values — not core relational graphs. |
| 9 | Future n8n? | Add `automation_jobs` later keyed to `project_id` / `section_id`; no project redesign. |
| 10 | Future workspaces? | **Not implemented.** Schema can gain `workspaces` + nullable/required `workspace_id` on users & projects without replacing core tables. See decisions doc. |
