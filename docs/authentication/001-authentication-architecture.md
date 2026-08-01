# Authentication Architecture (M2B)

## Scope

M2B introduces **users and JWT authentication** only.

Not included (future milestones):

- Roles / permissions / RBAC
- Audit logs
- Password reset / email verification
- OAuth / social login
- Refresh-token persistence / revocation tables
- Public self-registration

## Authentication flow

```text
Client
  │
  │  POST /auth/login { email, password }
  ▼
Auth router
  │
  ▼
user_service.authenticate_user
  │  normalize email
  │  load user
  │  reject inactive / bad password (same error)
  │  Argon2id verify
  ▼
create_access_token (JWT)
  │
  ▼
{ access_token, token_type: "bearer" }
```

Protected routes:

```text
Authorization: Bearer <access_token>
        │
        ▼
get_current_user dependency
        │  decode JWT
        │  load user by sub
        │  require is_active
        ▼
route handler (e.g. GET /auth/me)
```

## Password hashing

- Algorithm: **Argon2id** via `argon2-cffi`
- Plaintext passwords are hashed in `create_user` before insert
- Verification uses constant-time library checks
- Plaintext passwords are never logged or returned
- `password_hash` is never included in API schemas

## JWT flow

Configured via environment:

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Signing secret (required; no production default) |
| `JWT_ALGORITHM` | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default `60` |

Claims:

- `sub` — user UUID
- `iat` — issued at
- `exp` — expiry

If `JWT_SECRET_KEY` is missing, token create/decode fails safely (`RuntimeError` / 503 on login).

## Current-user dependency

`app/api/deps.py::get_current_user`:

1. Requires `Authorization: Bearer …`
2. Decodes JWT
3. Loads user from DB
4. Rejects missing/inactive users with generic 401

## Inactive users

- Cannot log in (same generic error as bad credentials)
- Existing tokens fail on `/auth/me` and other protected routes

## User creation (controlled)

No public `/auth/register`.

`user_service.create_user` is for:

- local bootstrap CLI
- future admin APIs
- internal tooling

## Future RBAC integration

Users intentionally have **no `role_id`**.

Later:

```text
User → UserRole → Role → RolePermission → Permission
```

AuthN (this milestone) stays separate from AuthZ (RBAC).

## Security decisions

1. Generic login errors (no email enumeration)
2. Argon2id instead of plaintext or reversible encryption
3. JWT secret required from environment
4. Response schemas exclude `password_hash`
5. `.env` ignored; `.env.example` placeholders only
