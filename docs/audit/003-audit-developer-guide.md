# Audit Developer Guide

## DO

- Record meaningful **business** actions (`user.created`, `role.assigned`, …)
- Use stable action codes from `app/audit/actions.py`
- Pass only safe metadata you intentionally construct
- Call `record_audit_event(...)` in the **same DB transaction** as the mutation, then `commit` once
- Leave `actor_user_id=None` for true system actions

Example:

```python
db.add(entity)
db.flush()
record_audit_event(
    db,
    actor_user_id=actor.id,
    action=ACTION_USER_CREATED,
    entity_type=ENTITY_USER,
    entity_id=entity.id,
    metadata={"email": entity.email},
)
db.commit()
```

## DO NOT

- Log passwords, password hashes, JWTs, refresh tokens, API keys
- Log Authorization headers or cookies
- Accept client-submitted arbitrary audit payloads
- Audit every SQL query / session open
- Provide update/delete APIs for audit logs
- Silently strip sensitive metadata keys — reject them

## Reading audits

```http
GET /audit-logs?page=1&page_size=20&action=user.created
```

Requires permission: `audit.view`

## Request context

```python
from app.audit.context import extract_request_audit_context

ctx = extract_request_audit_context(request)
record_audit_event(..., ip_address=ctx.ip_address, user_agent=ctx.user_agent)
```
