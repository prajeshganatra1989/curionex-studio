# Curionex Studio — Entity Relationship Diagram (v0.1)

Companion to [001-database-architecture.md](./001-database-architecture.md).

This diagram covers **MVP REQUIRED** tables and relationships. Future entities (`workspaces`, `automation_jobs`, etc.) are omitted for readability.

---

## Mermaid ER diagram

```mermaid
erDiagram
    users ||--o{ user_roles : has
    roles ||--o{ user_roles : assigned_to
    roles ||--o{ role_permissions : grants
    permissions ||--o{ role_permissions : granted_by

    users ||--o{ projects : owns
    users ||--o{ projects : creates
    categories ||--o{ projects : classifies
    projects ||--o{ project_tags : tagged
    tags ||--o{ project_tags : used_by
    projects ||--o{ project_members : assigns
    users ||--o{ project_members : member_of

    projects ||--|| knowledge_packs : contains
    knowledge_packs ||--o{ knowledge_pack_sections : has
    knowledge_pack_sections ||--o{ content_versions : versions
    knowledge_pack_sections }o--o| content_versions : current_version

    projects ||--o{ comments : has
    knowledge_pack_sections ||--o{ comments : discusses
    users ||--o{ comments : authors
    comments ||--o{ comments : parent_of

    projects ||--o{ approvals : tracks
    knowledge_pack_sections ||--o{ approvals : reviews
    content_versions ||--o{ approvals : submitted_as
    users ||--o{ approvals : submits
    users ||--o{ approvals : reviews

    projects ||--o{ attachments : has
    knowledge_pack_sections ||--o{ attachments : attaches
    users ||--o{ attachments : uploads

    users ||--o{ audit_logs : acts
    users ||--o{ user_preferences : prefers

    users {
        uuid id PK
        citext email UK
        varchar full_name
        varchar password_hash
        boolean is_active
        timestamptz last_login_at
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    roles {
        uuid id PK
        varchar code UK
        varchar name
        boolean is_system
        timestamptz deleted_at
    }

    permissions {
        uuid id PK
        varchar code UK
        varchar resource
        varchar action
    }

    user_roles {
        uuid user_id PK_FK
        uuid role_id PK_FK
        uuid assigned_by_id FK
        timestamptz assigned_at
    }

    role_permissions {
        uuid role_id PK_FK
        uuid permission_id PK_FK
        timestamptz created_at
    }

    categories {
        uuid id PK
        varchar name
        varchar slug UK
        timestamptz deleted_at
    }

    tags {
        uuid id PK
        varchar name
        varchar slug UK
        timestamptz deleted_at
    }

    projects {
        uuid id PK
        varchar crx_id UK
        varchar title
        text description
        int season
        int episode
        uuid category_id FK
        varchar status
        varchar priority
        uuid owner_id FK
        uuid created_by_id FK
        timestamptz deleted_at
    }

    project_tags {
        uuid project_id PK_FK
        uuid tag_id PK_FK
    }

    project_members {
        uuid id PK
        uuid project_id FK
        uuid user_id FK
        varchar assignment_role
        uuid assigned_by_id FK
    }

    knowledge_packs {
        uuid id PK
        uuid project_id FK_UK
        varchar status
        timestamptz deleted_at
    }

    knowledge_pack_sections {
        uuid id PK
        uuid knowledge_pack_id FK
        varchar section_type
        varchar status
        uuid current_version_id FK
        uuid created_by_id FK
        uuid updated_by_id FK
        timestamptz deleted_at
    }

    content_versions {
        uuid id PK
        varchar entity_type
        uuid entity_id
        varchar version_label
        int version_major
        int version_minor
        text content
        text change_summary
        uuid previous_version_id FK
        boolean is_current
        uuid created_by_id FK
        timestamptz created_at
    }

    comments {
        uuid id PK
        uuid project_id FK
        uuid section_id FK
        uuid author_id FK
        text body
        uuid parent_comment_id FK
        boolean is_resolved
        uuid resolved_by_id FK
        timestamptz deleted_at
    }

    approvals {
        uuid id PK
        uuid project_id FK
        uuid section_id FK
        uuid content_version_id FK
        varchar status
        uuid submitted_by_id FK
        uuid reviewer_id FK
        text decision_reason
        timestamptz submitted_at
        timestamptz decided_at
    }

    audit_logs {
        uuid id PK
        uuid actor_id FK
        varchar action
        varchar entity_type
        uuid entity_id
        inet ip_address
        varchar user_agent
        jsonb metadata
        jsonb old_values
        jsonb new_values
        timestamptz created_at
    }

    attachments {
        uuid id PK
        uuid project_id FK
        uuid section_id FK
        uuid uploaded_by_id FK
        varchar file_name
        varchar content_type
        bigint byte_size
        varchar storage_key UK
        char checksum_sha256
        timestamptz deleted_at
    }

    system_settings {
        uuid id PK
        varchar key UK
        jsonb value
        uuid updated_by_id FK
    }

    user_preferences {
        uuid id PK
        uuid user_id FK
        varchar key
        jsonb value
    }
```

---

## Relationship notes

1. **`content_versions.entity_id`** is a logical reference (MVP target: `knowledge_pack_sections.id`). It is not drawn as a hard FK to avoid polymorphic constraints.
2. **`knowledge_pack_sections.current_version_id`** is the only hard link from section → “active” version; create carefully to avoid migration ordering issues.
3. **`audit_logs.entity_id`** is likewise logical; only `actor_id` is a real FK to `users`.
4. **`comments.parent_comment_id`** enables future threads; MVP may treat all comments as top-level.
5. **`system_settings`** has no required parent entity; optional `updated_by_id` only.
