"""Editorial Library API tests."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.cli.seed_editorial_topics import seed_editorial_topics as seed_topics
from app.core.security import create_access_token
from app.editorial.seed_catalog import SEED_TOPICS
from app.models.editorial import EditorialTopic
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Edit",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str | None = None):
    seed_rbac_catalog(db)
    user = _user(db, email or f"owner-ed-{uuid4().hex[:8]}@example.com")
    rbac_service.assign_owner_role(db, user)
    return user


def _role_user(db: Session, email: str, role_name: str):
    seed_rbac_catalog(db)
    user = _user(db, email)
    role = rbac_service.get_role_by_name(db, role_name)
    assert role is not None
    assign_role_to_user(db, user_id=user.id, role_id=role.id)
    return user


def _topic_payload(**overrides):
    base = {
        "title": "Why Do We Dream?",
        "category": "Human Brain",
        "description": "A short exploration of dream science.",
        "difficulty": "easy",
        "evergreen_score": 80,
        "curiosity_score": 85,
        "viral_potential": "high",
    }
    base.update(overrides)
    return base


def test_editorial_crud_search_filters_and_archive(
    client: TestClient, db_session: Session
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)

    created = client.post(
        "/editorial-topics", headers=headers, json=_topic_payload()
    )
    assert created.status_code == 201, created.text
    body = created.json()
    topic = body["topic"]
    assert topic["status"] == "idea"
    assert topic["slug"]
    assert body["duplicate_warning"] is None
    topic_id = topic["id"]

    listed = client.get(
        "/editorial-topics?search=Dream&category=Human%20Brain&difficulty=easy"
        "&min_evergreen_score=70&sort=evergreen_desc",
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] >= 1
    assert any(item["id"] == topic_id for item in listed.json()["items"])

    patched = client.patch(
        f"/editorial-topics/{topic_id}",
        headers=headers,
        json={"status": "planned", "evergreen_score": 90},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["status"] == "planned"
    assert patched.json()["evergreen_score"] == 90

    archived = client.delete(f"/editorial-topics/{topic_id}", headers=headers)
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "archived"

    default_list = client.get("/editorial-topics", headers=headers)
    assert all(item["id"] != topic_id for item in default_list.json()["items"])

    with_archived = client.get(
        "/editorial-topics?include_archived=true&status=archived", headers=headers
    )
    assert any(item["id"] == topic_id for item in with_archived.json()["items"])


def test_duplicate_title_warning(client: TestClient, db_session: Session) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    first = client.post(
        "/editorial-topics",
        headers=headers,
        json=_topic_payload(title="Black Holes Explained Simply"),
    )
    assert first.status_code == 201
    second = client.post(
        "/editorial-topics",
        headers=headers,
        json=_topic_payload(
            title="black holes explained simply!!!",
            slug="black-holes-explained-simply-2",
        ),
    )
    assert second.status_code == 201, second.text
    warning = second.json()["duplicate_warning"]
    assert warning is not None
    assert warning["similar_topic_id"] == first.json()["topic"]["id"]


def test_create_project_from_topic_status_transition(
    client: TestClient, db_session: Session
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    topic = client.post(
        "/editorial-topics",
        headers=headers,
        json=_topic_payload(title="Why Is Space Silent?"),
    ).json()["topic"]

    created = client.post(
        f"/editorial-topics/{topic['id']}/create-project",
        headers=headers,
        json={"name": "Why Is Space Silent?"},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["topic"]["status"] == "project_created"
    assert body["topic"]["linked_project_id"] == body["project"]["id"]
    assert body["project"]["name"] == "Why Is Space Silent?"

    again = client.post(
        f"/editorial-topics/{topic['id']}/create-project",
        headers=headers,
        json={},
    )
    assert again.status_code == 409


def test_editorial_permissions(client: TestClient, db_session: Session) -> None:
    writer = _role_user(db_session, "writer-ed@example.com", "Script Writer")
    writer_headers = _auth_header(writer)

    assert client.get("/editorial-topics", headers=writer_headers).status_code == 200
    denied = client.post(
        "/editorial-topics",
        headers=writer_headers,
        json=_topic_payload(title="Writer Cannot Create"),
    )
    assert denied.status_code == 403

    bare = _user(db_session, "bare-ed@example.com")
    seed_rbac_catalog(db_session)
    bare_headers = _auth_header(bare)
    assert client.get("/editorial-topics", headers=bare_headers).status_code == 403
    assert client.get("/editorial-topics").status_code == 401


def test_seed_editorial_topics_idempotent(db_session: Session) -> None:
    first = seed_topics(db_session)
    assert first["created"] == 100
    assert first["skipped"] == 0
    second = seed_topics(db_session)
    assert second["created"] == 0
    assert second["skipped"] == 100
    assert db_session.query(EditorialTopic).count() == 100
    assert len(SEED_TOPICS) == 100


def test_summary_counts(client: TestClient, db_session: Session) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    client.post(
        "/editorial-topics",
        headers=headers,
        json=_topic_payload(title="Available Idea One", status="idea"),
    )
    client.post(
        "/editorial-topics",
        headers=headers,
        json=_topic_payload(
            title="Planned Idea Two", status="planned", slug="planned-idea-two"
        ),
    )
    summary = client.get("/editorial-topics/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["available"] >= 2
    assert body["total_active"] >= 2
