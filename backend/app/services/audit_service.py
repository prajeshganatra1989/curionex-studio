"""Append-only audit event service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog

# Keys that must never appear in audit metadata.
SENSITIVE_METADATA_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "passwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "jwt",
        "authorization",
        "api_key",
        "apikey",
        "cookie",
        "cookies",
        "credential",
        "credentials",
    }
)


class SensitiveAuditMetadataError(ValueError):
    """Raised when audit metadata contains forbidden sensitive keys."""


def _assert_safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        raise TypeError("Audit metadata must be a dict or None.")

    lowered = {str(key).lower() for key in metadata}
    banned = lowered & SENSITIVE_METADATA_KEYS
    if banned:
        raise SensitiveAuditMetadataError(
            f"Audit metadata contains forbidden keys: {sorted(banned)}"
        )
    return metadata


def record_audit_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Insert an audit event into the current transaction (flush only).

    Callers must ``commit`` (or roll back) the surrounding business transaction.
    This function does **not** commit on its own so audit rows participate in
    the same transaction as the related business change.
    """
    safe_metadata = _assert_safe_metadata(metadata)
    event = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        event_metadata=safe_metadata,
    )
    db.add(event)
    db.flush()
    return event


def list_audit_logs(
    db: Session,
    *,
    actor_user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditLog], int]:
    """Return paginated audit logs with optional filters."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    filters = []
    if actor_user_id is not None:
        filters.append(AuditLog.actor_user_id == actor_user_id)
    if action is not None:
        filters.append(AuditLog.action == action)
    if entity_type is not None:
        filters.append(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        filters.append(AuditLog.entity_id == entity_id)
    if created_from is not None:
        filters.append(AuditLog.created_at >= created_from)
    if created_to is not None:
        filters.append(AuditLog.created_at <= created_to)

    count_stmt = select(func.count()).select_from(AuditLog)
    list_stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)

    total = int(db.scalar(count_stmt) or 0)
    offset = (page - 1) * page_size
    items = list(db.scalars(list_stmt.offset(offset).limit(page_size)).all())
    return items, total
