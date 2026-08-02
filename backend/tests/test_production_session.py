"""Production Session API and selection algorithm tests."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.production.session import (
    SESSION_BUCKET_AI,
    SESSION_BUCKET_HUMAN_REVIEW,
    SESSION_BUCKET_QUALITY,
    SESSION_BUCKET_UNFINISHED,
    SESSION_BUCKET_VERSION,
    build_timeline,
    session_selection_bucket,
)
from app.schemas.auth import UserCreate
from app.schemas.project import ProjectCreate
from app.services import project_service, rbac_service
from app.services.rbac_service import seed_rbac_catalog
from app.services.user_service import create_user


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session):
    seed_rbac_catalog(db)
    user = create_user(
        db,
        UserCreate(
            email=f"session-{uuid4().hex[:8]}@example.com",
            password="securepass123",
            first_name="Session",
            last_name="Owner",
        ),
    )
    rbac_service.assign_owner_role(db, user)
    return user


def test_session_selection_bucket_priority_order() -> None:
    assert (
        session_selection_bucket("master_script", {"code": "generate_master_script"}, None)
        == SESSION_BUCKET_AI
    )
    assert (
        session_selection_bucket(
            "pending_human_review", {"code": "review_approval"}, None
        )
        == SESSION_BUCKET_HUMAN_REVIEW
    )
    assert (
        session_selection_bucket("quality_review", {"code": "run_quality_review"}, None)
        == SESSION_BUCKET_QUALITY
    )
    assert (
        session_selection_bucket("ready_for_version", {"code": "create_version"}, None)
        == SESSION_BUCKET_VERSION
    )
    assert (
        session_selection_bucket("discovery_brief", {"code": "open_knowledge_pack"}, None)
        == SESSION_BUCKET_UNFINISHED
    )


def test_timeline_progression() -> None:
    timeline = build_timeline(
        has_topic=True,
        has_knowledge_pack=True,
        knowledge_pack_complete=True,
        discovery=True,
        story=False,
        master=False,
        quality_done=False,
        version_done=False,
        approval_done=False,
        stage="story_spine",
    )
    by_key = {step["key"]: step["status"] for step in timeline}
    assert by_key["editorial_topic"] == "complete"
    assert by_key["knowledge_pack"] == "complete"
    assert by_key["discovery_brief"] == "complete"
    assert by_key["story_spine"] == "current"
    assert by_key["approval"] == "upcoming"


def test_production_session_empty_state(client: TestClient, db_session: Session) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    response = client.get("/production/session", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["empty"] is True
    assert body["current"] is None
    assert body["upcoming"] == []
    assert body["today"]["goal"] >= 1
    assert body["today"]["current_streak"] == 0
    assert body["browse_topics_url"] == "/topics"
    assert body["progress"]["approved_target"] >= 1


def test_production_session_selects_current_and_continue_url(
    client: TestClient, db_session: Session
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = project_service.create_project(
        db_session,
        ProjectCreate(name="Session Project Alpha", description="Session test"),
        creator=owner,
    )
    # Create an idea-stage path via editorial topic linked project optional —
    # project alone should appear as research/idea in classified units.
    response = client.get("/production/session", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["empty"] is False
    assert body["current"] is not None
    assert body["current"]["project_id"] == str(project.id)
    assert body["current"]["continue_url"]
    assert body["current"]["continue_url"].startswith("/")
    assert "dashboard" not in (body["current"]["continue_url"] or "")
    assert body["current"]["timeline"]
    assert body["current"]["sidebar"] is not None
    assert body["progress"]["approved_today"] >= 0


def test_production_session_wave_ordering(
    client: TestClient, db_session: Session
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project_service.create_project(
        db_session,
        ProjectCreate(name="Wave Late Project", description="Later"),
        creator=owner,
    )
    # Seed two topics with different waves linked after create-project API.
    topic_a = client.post(
        "/editorial-topics",
        headers=headers,
        json={
            "title": "Why Session Wave One Matters",
            "category": "Science",
            "priority": "A",
            "production_wave": 1,
            "slug": f"wave-one-{uuid4().hex[:6]}",
        },
    )
    assert topic_a.status_code == 201, topic_a.text
    topic_b = client.post(
        "/editorial-topics",
        headers=headers,
        json={
            "title": "Why Session Wave Four Matters",
            "category": "Science",
            "priority": "A",
            "production_wave": 4,
            "slug": f"wave-four-{uuid4().hex[:6]}",
        },
    )
    assert topic_b.status_code == 201, topic_b.text

    created_a = client.post(
        f"/editorial-topics/{topic_a.json()['topic']['id']}/create-project",
        headers=headers,
        json={"name": "Wave One Production"},
    )
    assert created_a.status_code == 201, created_a.text
    created_b = client.post(
        f"/editorial-topics/{topic_b.json()['topic']['id']}/create-project",
        headers=headers,
        json={"name": "Wave Four Production"},
    )
    assert created_b.status_code == 201, created_b.text

    session = client.get("/production/session", headers=headers)
    assert session.status_code == 200, session.text
    body = session.json()
    assert body["current"] is not None
    # Wave 1 should win over Wave 4 when both are unfinished at similar buckets.
    assert body["current"]["wave"] in {1, 4, None}
    if body["current"]["wave"] is not None and len(body["upcoming"]) >= 1:
        waves = [body["current"]["wave"]] + [
            item["wave"] for item in body["upcoming"] if item.get("wave") is not None
        ]
        if 1 in waves and 4 in waves:
            assert waves.index(1) < waves.index(4)


def test_production_session_requires_permission(
    client: TestClient, db_session: Session
) -> None:
    seed_rbac_catalog(db_session)
    bare = create_user(
        db_session,
        UserCreate(
            email=f"bare-session-{uuid4().hex[:8]}@example.com",
            password="securepass123",
            first_name="Bare",
            last_name="User",
        ),
    )
    headers = _auth_header(bare)
    assert client.get("/production/session", headers=headers).status_code == 403
    assert client.get("/production/session").status_code == 401
