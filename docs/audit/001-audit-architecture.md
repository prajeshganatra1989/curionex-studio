# Audit Architecture (M2D)

## Purpose

Append-only audit logging records meaningful **business** actions so Curionex Studio can answer who/what/when/where for security and operational review.

## Model

`audit_logs`

| Field | Notes |
|-------|-------|
| `id` | UUID PK |
| `actor_user_id` | Nullable FK → `users.id` (`ON DELETE SET NULL`) |
| `action` | Stable code (e.g. `user.created`) |
| `entity_type` | Logical type string |
| `entity_id` | Logical UUID (no polymorphic FK) |
| `created_at` | Indexed |
| `ip_address` | Optional `INET` |
| `user_agent` | Optional truncated string |
| `metadata` | JSONB (Python attr: `event_metadata`) |

## Actors

- **Human actor:** `actor_user_id` set to the authenticated user
- **System actor:** `actor_user_id = NULL` (future automation / n8n / workers)

## Entity references

We intentionally use `entity_type` + `entity_id` instead of polymorphic foreign keys so one table can reference many future entity kinds without schema breakage.

Application-level integrity is acceptable for audit references.

## Append-only

The application only **creates** and **reads** audit events.

There is no public API to update or delete audit logs, and no client-facing create endpoint for arbitrary audit submission.

## Transactions

`record_audit_event` **flushes** into the current session and does **not** commit.

Business mutation + audit insert should share one commit. If the transaction rolls back, the audit row does not falsely claim success.

If the audit insert fails (including sensitive-metadata rejection), the surrounding transaction should fail with the business change.

## Request context

Only IP address and User-Agent are captured.

Never store Authorization headers, cookies, tokens, or credential-bearing bodies.

## Security rules

Audit metadata must not include passwords, hashes, JWTs, API keys, or secrets.

Forbidden keys raise `SensitiveAuditMetadataError` rather than being silently stripped.
