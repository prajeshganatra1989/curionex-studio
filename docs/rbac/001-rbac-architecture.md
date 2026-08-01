# RBAC Architecture (M2C)

## Overview

Curionex Studio authorization is **permission-code driven** and stored in the database:

```text
User
  ↓ user_roles
Role (must be active)
  ↓ role_permissions
Permission (must be active; identified by code)
```

Application code checks **permission codes**, never role names.

```python
# Correct
require_permission("projects.create")

# Incorrect — do not do this
if user.role.name == "Admin":
    ...
```

## Authentication vs authorization

| Concern | Status | Meaning |
|---------|--------|---------|
| Authentication | `401 Unauthorized` | Missing/invalid/expired token, or inactive user |
| Authorization | `403 Forbidden` | Valid user, missing required permission |

## Components

| Piece | Location |
|-------|----------|
| Models | `app/models/rbac.py` |
| Catalog seed data | `app/rbac/catalog.py` |
| Service | `app/services/rbac_service.py` |
| Dependency | `app/api/deps.py::require_permission` |
| Routes | `app/api/routes/rbac.py` |
| Seed CLI | `python -m app.cli.seed_rbac` |
| Owner bootstrap | `python -m app.cli.create_user ... --assign-owner` |

## `has_permission` rules

A user is authorized for a code only when:

1. The user exists and `is_active` is true
2. At least one assigned role is `is_active`
3. That role is linked to a permission whose `code` matches exactly
4. That permission is `is_active`

Multiple roles combine (union of permission codes).

## Management API (minimal)

Protected by RBAC itself:

| Method | Path | Permission |
|--------|------|------------|
| GET | `/roles` | `roles.view` |
| GET | `/permissions` | `roles.view` |
| POST | `/roles` | `roles.create` |
| POST | `/roles/{role_id}/permissions/{permission_id}` | `roles.update` |
| POST | `/users/{user_id}/roles/{role_id}` | `roles.assign` |
| DELETE | `/users/{user_id}/roles/{role_id}` | `roles.assign` |

## Extensibility

- Add permissions to the catalog and seed again (idempotent)
- Create custom roles via API/service and grant permission codes
- Future feature modules should call `require_permission("<resource>.<action>")`

Roles remain editable data — not compiled constants in route handlers.
