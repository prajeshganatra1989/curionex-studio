# Curionex Studio — Database Decisions (v0.1)

This document records **why** key database choices were made.  
Schema detail lives in [../database/001-database-architecture.md](../database/001-database-architecture.md).

Scope: architecture decisions only. No migrations or models in this change.

---

## D1. UUID primary keys everywhere (application entities)

**Decision:** Use `UUID` primary keys (`gen_random_uuid()`).

**Why:**

- Safe to generate IDs in the API before insert.
- Avoids leaking sequential volume via public IDs.
- Merges cleanly if workspaces / distributed writers appear later.

**Tradeoff:** Slightly larger indexes than `BIGINT`; acceptable for this product scale.

---

## D2. Project ownership and assignment are separate

**Decision:**

- `projects.created_by_id` — historical creator  
- `projects.owner_id` — accountable owner (changeable)  
- `project_members` — collaborators / assignees  

**Why:** Creator, owner, and working assignees answer different questions (“who made it?”, “who is responsible?”, “who is working on it?”). Collapsing them into one field forces awkward role reuse and breaks audit clarity.

**MVP note:** `assignment_role` on members is a label only; authorization remains global RBAC.

---

## D3. Knowledge Pack sections are rows, not project columns

**Decision:** `projects` → `knowledge_packs` (1:1) → `knowledge_pack_sections` (1:N by `section_type`).

**Why:**

- Workflow sections share status, authorship, versions, approvals, and comments.
- Column-per-section on `projects` does not scale (new section types, independent lifecycle).
- A pack container allows pack-level metadata later without widening `projects`.

**Rejected alternative:** JSON document for the whole pack — weak constraints, poor versioning/approvals.

---

## D4. Generic immutable `content_versions`

**Decision:** One `content_versions` table with `entity_type` + `entity_id`, full text snapshots, linked list via `previous_version_id`, and `is_current`.

**Why:**

- Supports “who / when / what / previous / current / approved” without overwriting history.
- Same mechanism can version future artifacts (prompts, production notes) without a second subsystem.
- Full snapshots are simpler and safer than diff-only storage for editorial content.

**Why not a hard FK to sections only?** A section-only FK is cleaner for MVP purity, but the product explicitly needs a **generic** approach. Logical references + service validation are the compromise.

**Circular reference:** `current_version_id` on sections ↔ versions pointing at sections. Resolve with deferred FK or two-step migration when implementing.

---

## D5. Approvals are append-only and version-scoped

**Decision:** Each approval event is a new `approvals` row tied to `content_version_id`, `section_id`, and `project_id`.

**Why:**

- Approval history must survive subsequent decisions.
- Approving “the section” without a version is ambiguous after edits.
- Locking is a section status + permission concern; the approval row records the decision that led there.

**Product rule (recommended):** Creating a new version after approval returns the section toward draft / requires re-review.

---

## D6. Audit logs use logical entity references

**Decision:** `audit_logs` stores `entity_type` + `entity_id` without polymorphic foreign keys. Only `actor_id` is a real FK (`ON DELETE SET NULL`).

**Why:**

- Audits must outlive or tolerate missing targets (deleted projects, failed logins with no user).
- Polymorphic FKs are not native in PostgreSQL without complex constraints.
- Append-only + JSONB `old_values` / `new_values` provides reconstructable history.

**Security:** Application redaction is mandatory before write — no passwords, tokens, or API secrets.

---

## D7. Soft delete vs immutable tables

**Decision:**

| Soft delete | Never soft-delete / never mutate |
|-------------|----------------------------------|
| Users, roles, taxonomy, projects, packs, sections, comments, attachments | Audit logs, content versions, approval decision history |

**Why:** Collaborative content benefits from restore/trash semantics. Compliance and editorial integrity require immutable history streams.

---

## D8. JSONB only where flexibility is genuine

**Decision:** JSONB for `audit_logs` payloads, `system_settings.value`, `user_preferences.value`. Relational tables for users, RBAC, projects, sections, versions, approvals, comments.

**Why:** Core domain queries, FKs, and uniqueness belong in columns. JSONB is for variable attribute bags and change diffs.

**Rejected:** Storing Knowledge Pack bodies or RBAC maps as JSON blobs.

---

## D9. Configurable RBAC (no hard-coded role checks)

**Decision:** `roles`, `permissions`, `role_permissions`, `user_roles`. Authorize on **permission codes**.

**Why:** Owner may invent roles (contractors, freelancers) without code deploys. Example roles are seed data only.

**Rejected:** `users.role` enum column.

---

## D10. Categories vs tags

**Decision:** Optional single `category_id` on projects; many tags via `project_tags`.

**Why:** Matches the product framing (“one category, multiple tags”) while keeping both taxonomies editable tables.

---

## D11. Attachments store metadata only

**Decision:** `attachments` holds `storage_key`, MIME, size, checksum — not `BYTEA`.

**Why:** Files belong in filesystem/object storage (`storage/` or later S3). Database stays backup-friendly and query-fast.

---

## D12. Settings must not hold secrets

**Decision:** `system_settings` / `user_preferences` are non-secret configuration. Provider API keys remain in environment / secret managers.

**Why:** DB dumps, replicas, and broader `SELECT` grants must not become a secret store.

---

## D13. Status fields as VARCHAR (app-enforced)

**Decision:** Workflow statuses and section types are `VARCHAR`, not PostgreSQL ENUM types, for v0.1.

**Why:** ENUMs require awkward migrations to rename/add values. Application enums + check constraints (optional) are enough initially.

---

## D14. Future n8n / Studio Engine without redesign

**Decision:** Do **not** add automation tables in MVP. When needed, introduce something like:

`automation_jobs(id, project_id?, section_id?, provider, external_id, status, payload JSONB, created_at, …)`

**Why:** Jobs are an orchestration concern. Projects/sections already provide stable foreign anchors; no need to reshape content tables for n8n.

---

## D15. Multi-tenancy evolution path (not implemented)

**Decision:** Single-tenant schema for v0.1. Documented evolution:

```
workspaces
  └── workspace_members (user_id, role_in_workspace)
  └── projects.workspace_id
  └── users remain global or become workspace-scoped via membership
```

**Why this does not force a redesign now:**

- UUIDs and clear ownership tables already exist.
- Adding `workspace_id` (nullable → NOT NULL after backfill) to `projects`, taxonomy, and optionally settings is additive.
- RBAC can later become workspace-aware via `user_roles.workspace_id` or workspace roles — a migration, not a rewrite of versioning/approvals/audit.

**Explicit non-goal:** Do not add `workspace_id` columns until SaaS is a real requirement.

---

## D16. Comments: light threading hook

**Decision:** Include nullable `parent_comment_id` now; MVP UX may be flat.

**Why:** Avoids a breaking migration when threaded review is needed; cost is one nullable FK.

---

## Consistency review checklist

| Check | Result |
|-------|--------|
| Naming | `snake_case` tables/columns; plural table names |
| PK style | UUID across application entities |
| Creator vs owner vs members | Separated |
| Sections scalable | Row-based `section_type` |
| Versions multi-section | `entity_type`/`entity_id` + section `current_version_id` |
| Approvals preserve history | Append-only rows |
| RBAC custom roles | Table-driven permissions |
| Audit completeness | Action + entity + old/new JSONB + actor/time |
| Circular FKs | Only section ↔ current version; manageable at migration time |
| Multi-tenancy path | Additive `workspaces` later |
| n8n path | Additive `automation_jobs` later |

---

## Open product decisions (need human input)

These are intentional schema flex points, not blockers:

1. May soft-deleted `email` / `crx_id` values be reused? (partial unique indexes assume yes.)
2. After a new version is created post-approval, is re-approval mandatory?
3. Should inactive users be soft-deleted, `is_active=false` only, or both?
4. Is Knowledge Pack auto-created with all five section shells on project create?
5. When SaaS arrives, are users global identities or workspace-local accounts?
