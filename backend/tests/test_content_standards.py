"""Content Standard API and prompt-injection tests."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.prompt_renderer import render_template
from app.core.security import create_access_token
from app.editorial.content_standard_prompt import (
    format_content_standard,
    inject_content_standard_variables,
)
from app.editorial.content_standard_seed import CONTENT_STANDARD_V1
from app.models.audit import AuditLog
from app.models.content_standard import ContentStandard
from app.schemas.auth import UserCreate
from app.schemas.content_standard import ContentStandardCreate, ContentStandardUpdate
from app.services import content_standard_service, rbac_service
from app.services.content_standard_service import ensure_content_standard_v1
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Std",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str | None = None):
    seed_rbac_catalog(db)
    user = _user(db, email or f"owner-cs-{uuid4().hex[:8]}@example.com")
    rbac_service.assign_owner_role(db, user)
    return user


def _role_user(db: Session, email: str, role_name: str):
    seed_rbac_catalog(db)
    user = _user(db, email)
    role = rbac_service.get_role_by_name(db, role_name)
    assert role is not None
    assign_role_to_user(db, user_id=user.id, role_id=role.id)
    return user


def _payload(**overrides) -> dict:
    base = {
        "name": CONTENT_STANDARD_V1["name"],
        "version": "test-1",
        "status": "draft",
        "mission": CONTENT_STANDARD_V1["mission"],
        "target_audience": CONTENT_STANDARD_V1["target_audience"],
        "brand_voice": CONTENT_STANDARD_V1["brand_voice"],
        "editorial_principles": CONTENT_STANDARD_V1["editorial_principles"],
        "hook_rules": CONTENT_STANDARD_V1["hook_rules"],
        "story_structure": CONTENT_STANDARD_V1["story_structure"],
        "fact_policy": CONTENT_STANDARD_V1["fact_policy"],
        "citation_policy": CONTENT_STANDARD_V1["citation_policy"],
        "tone_guidelines": CONTENT_STANDARD_V1["tone_guidelines"],
        "language_rules": CONTENT_STANDARD_V1["language_rules"],
        "forbidden_patterns": CONTENT_STANDARD_V1["forbidden_patterns"],
        "approved_cta_patterns": CONTENT_STANDARD_V1["approved_cta_patterns"],
        "quality_checklist": CONTENT_STANDARD_V1["quality_checklist"],
        "default_duration_seconds": 60,
        "default_target_words": 160,
        "notes": "test",
    }
    base.update(overrides)
    return base


def test_ensure_seeds_single_active(db_session: Session):
    owner = _owner(db_session)
    first = ensure_content_standard_v1(db_session, actor=owner)
    second = ensure_content_standard_v1(db_session, actor=owner)
    assert first.id == second.id
    active = db_session.scalars(
        select(ContentStandard).where(ContentStandard.status == "active")
    ).all()
    assert len(active) == 1
    assert active[0].version == "1"
    assert "clarity" in active[0].mission.lower()


def test_activation_archives_previous(db_session: Session, client: TestClient):
    owner = _owner(db_session)
    v1 = ensure_content_standard_v1(db_session, actor=owner)
    create = client.post(
        "/content-standards",
        headers=_auth_header(owner),
        json=_payload(version="2", status="draft", name="Curionex Content Standard"),
    )
    assert create.status_code == 201, create.text
    v2_id = create.json()["id"]

    activate = client.post(
        f"/content-standards/{v2_id}/activate",
        headers=_auth_header(owner),
    )
    assert activate.status_code == 200, activate.text
    assert activate.json()["status"] == "active"

    db_session.refresh(v1)
    assert v1.status == "archived"
    active = client.get("/content-standards/active", headers=_auth_header(owner))
    assert active.status_code == 200
    assert active.json()["version"] == "2"
    assert active.json()["id"] == v2_id


def test_archive_standard(db_session: Session, client: TestClient):
    owner = _owner(db_session)
    ensure_content_standard_v1(db_session, actor=owner)
    created = client.post(
        "/content-standards",
        headers=_auth_header(owner),
        json=_payload(version="archive-me", status="draft"),
    )
    assert created.status_code == 201
    sid = created.json()["id"]
    archived = client.post(
        f"/content-standards/{sid}/archive",
        headers=_auth_header(owner),
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


def test_prompt_rendering_includes_standard(db_session: Session):
    owner = _owner(db_session)
    standard = ensure_content_standard_v1(db_session, actor=owner)
    variables = inject_content_standard_variables(db_session, {"topic": "gravity"})
    rendered = render_template(
        "Uses {{content_standard_label}}\n{{content_standard}}\nTopic: {{topic}}",
        variables,
    )
    assert f"{standard.name} v{standard.version}" in rendered
    assert standard.mission in rendered
    assert (
        "Never invent statistics" in rendered
        or "never invent statistics" in rendered.lower()
    )
    assert "Topic: gravity" in rendered


def test_prompt_rendering_updates_after_activation(db_session: Session):
    owner = _owner(db_session)
    ensure_content_standard_v1(db_session, actor=owner)
    v2 = content_standard_service.create_standard(
        db_session,
        ContentStandardCreate(
            **{
                **CONTENT_STANDARD_V1,
                "version": "2",
                "status": "draft",
                "mission": "Version two mission about wonder.",
            }
        ),
        actor=owner,
    )
    before = inject_content_standard_variables(db_session, {})
    assert "Version two mission" not in before["content_standard"]

    content_standard_service.activate_standard(db_session, v2.id, actor=owner)
    after = inject_content_standard_variables(db_session, {})
    assert after["content_standard_version"] == "2"
    assert "Version two mission about wonder." in after["content_standard"]
    rendered = render_template("{{content_standard}}", after)
    assert "Version two mission about wonder." in rendered


def test_only_one_active_via_create(db_session: Session, client: TestClient):
    owner = _owner(db_session)
    ensure_content_standard_v1(db_session, actor=owner)
    response = client.post(
        "/content-standards",
        headers=_auth_header(owner),
        json=_payload(version="3", status="active", mission="Third active attempt."),
    )
    assert response.status_code == 201
    active_rows = db_session.scalars(
        select(ContentStandard).where(ContentStandard.status == "active")
    ).all()
    assert len(active_rows) == 1
    assert active_rows[0].version == "3"


def test_rbac_view_and_manage(db_session: Session, client: TestClient):
    seed_rbac_catalog(db_session)
    writer = _role_user(
        db_session, f"writer-cs-{uuid4().hex[:8]}@example.com", "Script Writer"
    )
    reviewer = _role_user(
        db_session, f"reviewer-cs-{uuid4().hex[:8]}@example.com", "Reviewer"
    )
    manager = _role_user(
        db_session, f"cm-cs-{uuid4().hex[:8]}@example.com", "Content Manager"
    )
    owner = _owner(db_session, f"owner-rbac-cs-{uuid4().hex[:8]}@example.com")
    ensure_content_standard_v1(db_session, actor=owner)

    for user in (writer, reviewer, manager, owner):
        listed = client.get("/content-standards", headers=_auth_header(user))
        assert listed.status_code == 200, listed.text

    denied = client.post(
        "/content-standards",
        headers=_auth_header(writer),
        json=_payload(version="writer-denied"),
    )
    assert denied.status_code == 403

    allowed = client.post(
        "/content-standards",
        headers=_auth_header(manager),
        json=_payload(version="manager-ok"),
    )
    assert allowed.status_code == 201, allowed.text


def test_audit_events_for_lifecycle(db_session: Session):
    owner = _owner(db_session)
    standard = ensure_content_standard_v1(db_session, actor=owner)
    content_standard_service.update_standard(
        db_session,
        standard.id,
        ContentStandardUpdate(notes="updated note"),
        actor=owner,
    )
    v2 = content_standard_service.create_standard(
        db_session,
        ContentStandardCreate(
            **{**CONTENT_STANDARD_V1, "version": "audit-2", "status": "draft"}
        ),
        actor=owner,
    )
    content_standard_service.activate_standard(db_session, v2.id, actor=owner)
    content_standard_service.archive_standard(db_session, v2.id, actor=owner)

    actions = {
        row.action
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.entity_type == "content_standard")
        ).all()
    }
    assert "content_standard.created" in actions
    assert "content_standard.updated" in actions
    assert "content_standard.activated" in actions
    assert "content_standard.archived" in actions


def test_format_includes_core_sections(db_session: Session):
    owner = _owner(db_session)
    standard = ensure_content_standard_v1(db_session, actor=owner)
    text = format_content_standard(standard)
    for heading in (
        "## Mission",
        "## Brand voice",
        "## Hook rules",
        "## Fact policy",
        "## Quality checklist",
    ):
        assert heading in text


def test_summary_and_empty_active(db_session: Session, client: TestClient):
    owner = _owner(db_session)
    # Clear any session-external active seed so empty-state is observable.
    for row in db_session.scalars(
        select(ContentStandard).where(ContentStandard.status == "active")
    ).all():
        row.status = "archived"
    db_session.flush()

    empty = client.get("/content-standards/summary", headers=_auth_header(owner))
    assert empty.status_code == 200
    assert empty.json()["has_active"] is False

    missing = client.get("/content-standards/active", headers=_auth_header(owner))
    assert missing.status_code == 404

    ensure_content_standard_v1(db_session, actor=owner)
    summary = client.get("/content-standards/summary", headers=_auth_header(owner))
    assert summary.status_code == 200
    body = summary.json()
    assert body["has_active"] is True
    assert body["version"] == "1"
    assert "Curionex Content Standard v1" in body["label"]
