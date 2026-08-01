"""Audit logging tests."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_AUTH_LOGIN,
    ACTION_AUTH_LOGIN_FAILED,
    ACTION_ROLE_ASSIGNED,
    ACTION_USER_CREATED,
    ACTION_USER_DEACTIVATED,
)
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.audit_service import (
    SensitiveAuditMetadataError,
    list_audit_logs,
    record_audit_event,
)
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user, deactivate_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Audit",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def test_audit_event_creation_and_fields(db_session: Session) -> None:
    user = _user(db_session, "audit-create@example.com")
    event = record_audit_event(
        db_session,
        actor_user_id=user.id,
        action="custom.test",
        entity_type="user",
        entity_id=user.id,
        metadata={"note": "ok"},
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    db_session.commit()
    assert event.id is not None
    assert event.actor_user_id == user.id
    assert event.action == "custom.test"
    assert event.entity_type == "user"
    assert event.entity_id == user.id
    assert event.event_metadata == {"note": "ok"}
    assert str(event.ip_address) == "127.0.0.1"


def test_system_audit_event_null_actor(db_session: Session) -> None:
    event = record_audit_event(
        db_session,
        actor_user_id=None,
        action="system.ping",
        entity_type="authentication",
        entity_id=None,
        metadata={"reason": "scheduled"},
    )
    db_session.commit()
    assert event.actor_user_id is None


def test_sensitive_metadata_rejected(db_session: Session) -> None:
    with pytest.raises(SensitiveAuditMetadataError):
        record_audit_event(
            db_session,
            action="bad.meta",
            entity_type="user",
            metadata={"password": "secret"},
        )


def test_user_creation_writes_audit(db_session: Session) -> None:
    user = _user(db_session, "created-audit@example.com")
    rows = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_USER_CREATED)
    ).all()
    assert any(row.entity_id == user.id for row in rows)


def test_login_success_and_failure_audit(
    client: TestClient,
    db_session: Session,
) -> None:
    create_user(
        db_session,
        UserCreate(
            email="login-audit@example.com",
            password="securepass123",
            first_name="Login",
            last_name="Audit",
        ),
    )
    ok = client.post(
        "/auth/login",
        json={"email": "login-audit@example.com", "password": "securepass123"},
    )
    bad = client.post(
        "/auth/login",
        json={"email": "login-audit@example.com", "password": "wrong-password"},
    )
    assert ok.status_code == 200
    assert bad.status_code == 401

    actions = {row.action for row in db_session.scalars(select(AuditLog)).all()}
    assert ACTION_AUTH_LOGIN in actions
    assert ACTION_AUTH_LOGIN_FAILED in actions

    failed = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_AUTH_LOGIN_FAILED)
    ).all()
    assert all(row.event_metadata == {"reason": "invalid_credentials"} for row in failed)
    serialized = str([row.event_metadata for row in failed]).lower()
    assert "password" not in serialized or "invalid_credentials" in serialized
    assert "securepass" not in serialized


def test_user_deactivation_audit(db_session: Session) -> None:
    user = _user(db_session, "deactivate-audit@example.com")
    deactivate_user(db_session, user.id, actor_user_id=user.id)
    rows = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_USER_DEACTIVATED)
    ).all()
    assert any(row.entity_id == user.id for row in rows)


def test_role_assignment_audit(db_session: Session) -> None:
    seed_rbac_catalog(db_session)
    actor = _user(db_session, "assigner@example.com")
    target = _user(db_session, "assignee@example.com")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert writer is not None
    assign_role_to_user(
        db_session,
        user_id=target.id,
        role_id=writer.id,
        actor_user_id=actor.id,
    )
    rows = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_ROLE_ASSIGNED)
    ).all()
    assert any(row.entity_id == target.id for row in rows)


def test_audit_api_requires_auth_and_permission(
    client: TestClient,
    db_session: Session,
) -> None:
    assert client.get("/audit-logs").status_code == 401

    seed_rbac_catalog(db_session)
    writer_user = _user(db_session, "writer-audit@example.com")
    writer = rbac_service.get_role_by_name(db_session, "Script Writer")
    assert writer is not None
    assign_role_to_user(db_session, user_id=writer_user.id, role_id=writer.id)
    assert (
        client.get("/audit-logs", headers=_auth_header(writer_user)).status_code == 403
    )

    owner = _user(db_session, "owner-audit@example.com")
    rbac_service.assign_owner_role(db_session, owner)
    response = client.get("/audit-logs", headers=_auth_header(owner))
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert body["page"] == 1
    assert "password" not in str(body).lower() or "password_hash" not in str(body).lower()
    assert "password_hash" not in str(body)


def test_audit_filtering_and_pagination(db_session: Session) -> None:
    user = _user(db_session, "filter-audit@example.com")
    for i in range(3):
        record_audit_event(
            db_session,
            actor_user_id=user.id,
            action=f"filter.action.{i}",
            entity_type="user",
            entity_id=user.id,
        )
    db_session.commit()

    items, total = list_audit_logs(
        db_session,
        actor_user_id=user.id,
        action="filter.action.1",
        page=1,
        page_size=10,
    )
    assert total >= 1
    assert all(item.action == "filter.action.1" for item in items)

    page_items, _ = list_audit_logs(db_session, page=1, page_size=2)
    assert len(page_items) <= 2


def test_no_public_audit_mutation_endpoints(client: TestClient) -> None:
    fake_id = uuid4()
    assert client.post("/audit-logs", json={}).status_code in {404, 405, 401, 422}
    assert client.put(f"/audit-logs/{fake_id}", json={}).status_code in {
        404,
        405,
        401,
        422,
    }
    assert client.delete(f"/audit-logs/{fake_id}").status_code in {404, 405, 401, 422}


def test_login_failure_metadata_has_no_secrets(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/auth/login",
        json={"email": "missing-user@example.com", "password": "whatever123"},
    )
    failed = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_AUTH_LOGIN_FAILED)
    ).all()
    assert failed
    for row in failed:
        blob = str(row.event_metadata).lower()
        assert "whatever123" not in blob
        assert "authorization" not in blob
        assert "bearer" not in blob
