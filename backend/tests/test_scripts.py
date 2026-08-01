"""Script workspace tests."""

import threading

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker

from app.audit.actions import (
    ACTION_SCRIPT_ARCHIVED,
    ACTION_SCRIPT_CREATED,
    ACTION_SCRIPT_DOCUMENT_UPDATED,
    ACTION_SCRIPT_UPDATED,
)
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.models.script import Script, ScriptDocument
from app.schemas.auth import UserCreate
from app.schemas.knowledge_pack import KnowledgePackCreate
from app.schemas.project import ProjectCreate
from app.schemas.script import ScriptCreate
from app.scripts.catalog import DOCUMENT_CATALOG
from app.services import knowledge_pack_service, rbac_service, script_service
from app.services.project_service import create_project
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Script",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-script@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _project(client: TestClient, headers: dict, name: str = "Script Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _create_script(
    client: TestClient,
    headers: dict,
    project_id: str,
    title: str = "Main Script",
    knowledge_pack_id: str | None = None,
) -> dict:
    payload: dict = {"title": title}
    if knowledge_pack_id is not None:
        payload["knowledge_pack_id"] = knowledge_pack_id
    response = client.post(
        f"/projects/{project_id}/scripts",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_script_creation_code_and_document_shells(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers)
    pack = client.post(
        f"/projects/{project['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Research Pack"},
    )
    assert pack.status_code == 201

    script = _create_script(
        client,
        headers,
        project["id"],
        knowledge_pack_id=pack.json()["id"],
    )
    assert script["project_id"] == project["id"]
    assert script["created_by"] == str(owner.id)
    assert script["status"] == "draft"
    assert script["knowledge_pack_id"] == pack.json()["id"]
    assert script["script_code"].startswith(f"{project['project_code']}-S")
    assert len(script["documents"]) == 3

    expected = [
        (item.document_type, item.position, item.title) for item in DOCUMENT_CATALOG
    ]
    actual = [
        (doc["document_type"], doc["position"], doc["title"])
        for doc in script["documents"]
    ]
    assert actual == expected
    assert all(doc["content"] == "" for doc in script["documents"])

    second = _create_script(client, headers, project["id"], title="Second")
    assert second["script_code"] != script["script_code"]
    assert second["script_code"].endswith("S02")


def test_cross_project_knowledge_pack_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-script-xpack@example.com")
    headers = _auth_header(owner)
    project_a = _project(client, headers, "Project A Scripts")
    project_b = _project(client, headers, "Project B Scripts")
    pack_b = client.post(
        f"/projects/{project_b['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Pack B"},
    ).json()

    response = client.post(
        f"/projects/{project_a['id']}/scripts",
        headers=headers,
        json={"title": "Bad Link", "knowledge_pack_id": pack_b["id"]},
    )
    assert response.status_code == 422


def test_list_detail_update_archive(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-script-life@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Lifecycle Scripts")
    for index in range(3):
        _create_script(client, headers, project["id"], title=f"Searchable {index}")

    listed = client.get(
        f"/projects/{project['id']}/scripts?page=1&page_size=2",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] >= 3
    assert len(listed.json()["items"]) == 2
    assert "documents" not in listed.json()["items"][0]

    searched = client.get(
        f"/projects/{project['id']}/scripts?search=Searchable%201",
        headers=headers,
    )
    assert searched.json()["total"] >= 1

    script_id = searched.json()["items"][0]["id"]
    detail = client.get(f"/scripts/{script_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["documents"]) == 3

    updated = client.patch(
        f"/scripts/{script_id}",
        headers=headers,
        json={"title": "Updated Title", "status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Updated Title"
    assert updated.json()["status"] == "in_progress"

    archived = client.delete(f"/scripts/{script_id}", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    still = db_session.get(Script, script_id)
    assert still is not None
    docs = db_session.scalars(
        select(ScriptDocument).where(ScriptDocument.script_id == script_id)
    ).all()
    assert len(docs) == 3


def test_document_get_and_update(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-script-docs@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Doc Project")
    script = _create_script(client, headers, project["id"])
    script_id = script["id"]

    docs = client.get(f"/scripts/{script_id}/documents", headers=headers)
    assert docs.status_code == 200
    assert [d["document_type"] for d in docs.json()] == [
        item.document_type for item in DOCUMENT_CATALOG
    ]

    for doc_type, body in [
        ("discovery_brief", "Discovery content"),
        ("story_spine", "Spine content"),
        ("master_script", "Master content"),
    ]:
        patched = client.patch(
            f"/scripts/{script_id}/documents/{doc_type}",
            headers=headers,
            json={"content": body, "title": doc_type.replace("_", " ").title()},
        )
        assert patched.status_code == 200
        assert patched.json()["content"] == body
        assert patched.json()["document_type"] == doc_type

    one = client.get(
        f"/scripts/{script_id}/documents/master_script",
        headers=headers,
    )
    assert one.json()["content"] == "Master content"


def test_rbac_and_project_access(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    writer = _user(db_session, "writer-script@example.com")
    writer_role = rbac_service.get_role_by_name(db_session, "Script Writer")
    assign_role_to_user(db_session, user_id=writer.id, role_id=writer_role.id)

    reviewer = _user(db_session, "reviewer-script@example.com")
    reviewer_role = rbac_service.get_role_by_name(db_session, "Reviewer")
    assign_role_to_user(db_session, user_id=reviewer.id, role_id=reviewer_role.id)

    owner = _owner(db_session, "owner-script-rbac@example.com")
    owner_headers = _auth_header(owner)
    writer_headers = _auth_header(writer)
    reviewer_headers = _auth_header(reviewer)

    project = _project(client, owner_headers, "RBAC Scripts")
    client.post(
        f"/projects/{project['id']}/members/{writer.id}",
        headers=owner_headers,
    )
    client.post(
        f"/projects/{project['id']}/members/{reviewer.id}",
        headers=owner_headers,
    )

    created = client.post(
        f"/projects/{project['id']}/scripts",
        headers=writer_headers,
        json={"title": "Writer Script"},
    )
    assert created.status_code == 201
    script_id = created.json()["id"]

    assert (
        client.post(
            f"/projects/{project['id']}/scripts",
            headers=reviewer_headers,
            json={"title": "Nope"},
        ).status_code
        == 403
    )
    assert (
        client.delete(f"/scripts/{script_id}", headers=writer_headers).status_code
        == 403
    )
    assert (
        client.get(f"/scripts/{script_id}", headers=reviewer_headers).status_code
        == 200
    )

    outsider = _owner(db_session, "outsider-script@example.com")
    assert (
        client.get(
            f"/scripts/{script_id}",
            headers=_auth_header(outsider),
        ).status_code
        == 403
    )
    assert client.get(f"/scripts/{script_id}").status_code == 401


def test_script_audit_without_full_content(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-script-audit@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Audit Scripts")
    script = _create_script(client, headers, project["id"])
    script_id = script["id"]

    client.patch(
        f"/scripts/{script_id}",
        headers=headers,
        json={"description": "notes"},
    )
    client.patch(
        f"/scripts/{script_id}/documents/discovery_brief",
        headers=headers,
        json={"content": "SECRET_DOC_BODY_SHOULD_NOT_APPEAR"},
    )
    client.delete(f"/scripts/{script_id}", headers=headers)

    events = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.action.in_(
                    [
                        ACTION_SCRIPT_CREATED,
                        ACTION_SCRIPT_UPDATED,
                        ACTION_SCRIPT_DOCUMENT_UPDATED,
                        ACTION_SCRIPT_ARCHIVED,
                    ]
                )
            )
        )
    )
    assert {e.action for e in events} >= {
        ACTION_SCRIPT_CREATED,
        ACTION_SCRIPT_UPDATED,
        ACTION_SCRIPT_DOCUMENT_UPDATED,
        ACTION_SCRIPT_ARCHIVED,
    }
    for event in events:
        meta = event.event_metadata or {}
        assert "SECRET_DOC_BODY_SHOULD_NOT_APPEAR" not in str(meta)
        assert "content" not in meta or meta.get("content") is None


def test_concurrent_script_code_allocation(engine) -> None:
    from uuid import uuid4

    from app.models.user import User

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup = SessionLocal()
    project_id = None
    creator_id = None
    project_code = None
    email = f"owner-script-concurrent-{uuid4().hex[:8]}@example.com"
    try:
        owner = _owner(setup, email)
        project = create_project(
            setup,
            ProjectCreate(name="Concurrent Scripts"),
            creator=owner,
        )
        project_id = project.id
        creator_id = owner.id
        project_code = project.project_code
    finally:
        setup.close()

    results: list[str] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        session = SessionLocal()
        try:
            barrier.wait(timeout=5)
            creator = session.get(User, creator_id)
            assert creator is not None
            script = script_service.create_script(
                session,
                project_id,
                ScriptCreate(title="Concurrent"),
                creator=creator,
            )
            results.append(script.script_code)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
            session.rollback()
        finally:
            session.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert not errors, errors
    assert sorted(results) == [
        f"{project_code}-S01",
        f"{project_code}-S02",
    ]

    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM script_documents WHERE script_id IN "
                "(SELECT id FROM scripts WHERE project_id = :pid)"
            ),
            {"pid": project_id},
        )
        connection.execute(
            text("DELETE FROM scripts WHERE project_id = :pid"),
            {"pid": project_id},
        )
        connection.execute(
            text("DELETE FROM project_members WHERE project_id = :pid"),
            {"pid": project_id},
        )
        connection.execute(
            text("DELETE FROM projects WHERE id = :pid"),
            {"pid": project_id},
        )
        connection.execute(
            text("DELETE FROM audit_logs WHERE actor_user_id = :uid"),
            {"uid": creator_id},
        )
        connection.execute(
            text("DELETE FROM user_roles WHERE user_id = :uid"),
            {"uid": creator_id},
        )
        connection.execute(
            text("DELETE FROM users WHERE id = :uid"),
            {"uid": creator_id},
        )


def test_service_knowledge_pack_same_project(db_session: Session) -> None:
    owner = _owner(db_session, "owner-script-svc@example.com")
    project = create_project(
        db_session,
        ProjectCreate(name="Svc Scripts"),
        creator=owner,
    )
    pack = knowledge_pack_service.create_knowledge_pack(
        db_session,
        project.id,
        KnowledgePackCreate(name="Pack"),
        creator=owner,
    )
    script = script_service.create_script(
        db_session,
        project.id,
        ScriptCreate(title="Linked", knowledge_pack_id=pack.id),
        creator=owner,
    )
    assert script.knowledge_pack_id == pack.id
