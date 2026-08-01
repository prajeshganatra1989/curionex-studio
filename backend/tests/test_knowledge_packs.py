"""Knowledge Pack foundation tests."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_KNOWLEDGE_PACK_ARCHIVED,
    ACTION_KNOWLEDGE_PACK_CREATED,
    ACTION_KNOWLEDGE_PACK_SECTION_UPDATED,
    ACTION_KNOWLEDGE_PACK_SECTIONS_REORDERED,
    ACTION_KNOWLEDGE_PACK_UPDATED,
)
from app.core.security import create_access_token
from app.knowledge_packs.catalog import SECTION_CATALOG, initial_section_definitions
from app.models.audit import AuditLog
from app.models.knowledge_pack import KnowledgePack, KnowledgePackSection
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
            first_name="Pack",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-kp@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _project(client: TestClient, headers: dict, name: str = "KP Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _create_pack(
    client: TestClient,
    headers: dict,
    project_id: str,
    name: str = "Main Pack",
) -> dict:
    response = client.post(
        f"/projects/{project_id}/knowledge-packs",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_knowledge_pack_with_section_shells(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers)
    pack = _create_pack(client, headers, project["id"])

    assert pack["project_id"] == project["id"]
    assert pack["created_by"] == str(owner.id)
    assert pack["status"] == "draft"
    assert len(pack["sections"]) == len(SECTION_CATALOG)

    expected = [(item.key, item.position, item.title) for item in SECTION_CATALOG]
    actual = [
        (section["section_key"], section["position"], section["title"])
        for section in pack["sections"]
    ]
    assert actual == expected
    assert all(section["content"] == "" for section in pack["sections"])


def test_list_pagination_status_and_search(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-kp-list@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "List Project")
    for index in range(3):
        _create_pack(client, headers, project["id"], name=f"Search Pack {index}")

    page = client.get(
        f"/projects/{project['id']}/knowledge-packs?page=1&page_size=2",
        headers=headers,
    )
    assert page.status_code == 200
    body = page.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert "sections" not in body["items"][0]

    by_name = client.get(
        f"/projects/{project['id']}/knowledge-packs?search=Search%20Pack%201",
        headers=headers,
    )
    assert by_name.status_code == 200
    assert by_name.json()["total"] >= 1

    active = client.post(
        f"/projects/{project['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Active Pack", "status": "active"},
    )
    assert active.status_code == 201
    filtered = client.get(
        f"/projects/{project['id']}/knowledge-packs?status=active",
        headers=headers,
    )
    assert any(item["id"] == active.json()["id"] for item in filtered.json()["items"])


def test_detail_update_archive_keeps_rows(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-kp-life@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Lifecycle Project")
    pack = _create_pack(client, headers, project["id"], "Lifecycle Pack")
    pack_id = pack["id"]

    detail = client.get(f"/knowledge-packs/{pack_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Lifecycle Pack"
    assert "password" not in detail.text.lower()

    updated = client.patch(
        f"/knowledge-packs/{pack_id}",
        headers=headers,
        json={"name": "Lifecycle Pack 2", "description": "notes"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Lifecycle Pack 2"

    archived = client.delete(f"/knowledge-packs/{pack_id}", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    still = db_session.get(KnowledgePack, pack_id)
    assert still is not None
    assert still.status == "archived"
    sections = db_session.scalars(
        select(KnowledgePackSection).where(
            KnowledgePackSection.knowledge_pack_id == pack_id
        )
    ).all()
    assert len(sections) == len(SECTION_CATALOG)


def test_section_get_update_and_reorder(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-kp-sections@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Section Project")
    pack = _create_pack(client, headers, project["id"], "Section Pack")
    pack_id = pack["id"]

    sections = client.get(f"/knowledge-packs/{pack_id}/sections", headers=headers)
    assert sections.status_code == 200
    assert [item["section_key"] for item in sections.json()] == [
        item.key for item in SECTION_CATALOG
    ]

    one = client.get(f"/knowledge-packs/{pack_id}/sections/research", headers=headers)
    assert one.status_code == 200
    assert one.json()["section_key"] == "research"

    patched = client.patch(
        f"/knowledge-packs/{pack_id}/sections/research",
        headers=headers,
        json={"title": "Deep Research", "content": "Background facts here."},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Deep Research"
    assert patched.json()["content"] == "Background facts here."

    reversed_keys = list(reversed([item.key for item in SECTION_CATALOG]))
    reordered = client.patch(
        f"/knowledge-packs/{pack_id}/sections/reorder",
        headers=headers,
        json=reversed_keys,
    )
    assert reordered.status_code == 200
    assert [item["section_key"] for item in reordered.json()] == reversed_keys
    assert [item["position"] for item in reordered.json()] == list(
        range(1, len(reversed_keys) + 1)
    )


def test_invalid_reorder_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-kp-reorder@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Reorder Project")
    pack = _create_pack(client, headers, project["id"])
    pack_id = pack["id"]
    keys = [item.key for item in SECTION_CATALOG]

    duplicate = client.patch(
        f"/knowledge-packs/{pack_id}/sections/reorder",
        headers=headers,
        json=keys + [keys[0]],
    )
    assert duplicate.status_code == 422

    unknown = client.patch(
        f"/knowledge-packs/{pack_id}/sections/reorder",
        headers=headers,
        json=keys[:-1] + ["not_a_section"],
    )
    assert unknown.status_code == 422

    partial = client.patch(
        f"/knowledge-packs/{pack_id}/sections/reorder",
        headers=headers,
        json=keys[:-1],
    )
    assert partial.status_code == 422


def test_rbac_and_unauthenticated(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    writer = _user(db_session, "writer-kp@example.com")
    writer_role = rbac_service.get_role_by_name(db_session, "Script Writer")
    assign_role_to_user(db_session, user_id=writer.id, role_id=writer_role.id)

    owner = _owner(db_session, "owner-kp-rbac@example.com")
    owner_headers = _auth_header(owner)
    writer_headers = _auth_header(writer)
    project = _project(client, owner_headers, "RBAC Project")
    # Add writer as member so membership is not the blocker.
    client.post(
        f"/projects/{project['id']}/members/{writer.id}",
        headers=owner_headers,
    )

    denied = client.post(
        f"/projects/{project['id']}/knowledge-packs",
        headers=writer_headers,
        json={"name": "Nope"},
    )
    assert denied.status_code == 403

    pack = _create_pack(client, owner_headers, project["id"])
    assert (
        client.patch(
            f"/knowledge-packs/{pack['id']}",
            headers=writer_headers,
            json={"name": "Hacked"},
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/knowledge-packs/{pack['id']}",
            headers=writer_headers,
        ).status_code
        == 403
    )
    # Script Writer has knowledge_packs.view? Looking at catalog - Script Writer has
    # knowledge_packs.view. So view should work.
    assert (
        client.get(
            f"/knowledge-packs/{pack['id']}",
            headers=writer_headers,
        ).status_code
        == 200
    )

    assert client.get(f"/knowledge-packs/{pack['id']}").status_code == 401


def test_project_access_requires_membership(
    client: TestClient,
    db_session: Session,
) -> None:
    owner_a = _owner(db_session, "owner-a-kp@example.com")
    owner_b = _owner(db_session, "owner-b-kp@example.com")
    headers_a = _auth_header(owner_a)
    headers_b = _auth_header(owner_b)

    project_a = _project(client, headers_a, "Project A")
    pack = _create_pack(client, headers_a, project_a["id"], "Pack A")

    # Owner B has global knowledge_packs permissions but is not a member of A.
    forbidden = client.get(f"/knowledge-packs/{pack['id']}", headers=headers_b)
    assert forbidden.status_code == 403

    create_denied = client.post(
        f"/projects/{project_a['id']}/knowledge-packs",
        headers=headers_b,
        json={"name": "Intruder"},
    )
    assert create_denied.status_code == 403


def test_content_manager_create_without_delete(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    manager = _user(db_session, "manager-kp@example.com")
    role = rbac_service.get_role_by_name(db_session, "Content Manager")
    assign_role_to_user(db_session, user_id=manager.id, role_id=role.id)
    owner = _owner(db_session, "owner-for-manager-kp@example.com")
    owner_headers = _auth_header(owner)
    manager_headers = _auth_header(manager)

    project = _project(client, owner_headers, "Manager Project")
    client.post(
        f"/projects/{project['id']}/members/{manager.id}",
        headers=owner_headers,
    )

    created = client.post(
        f"/projects/{project['id']}/knowledge-packs",
        headers=manager_headers,
        json={"name": "CM Pack"},
    )
    assert created.status_code == 201
    pack_id = created.json()["id"]

    updated = client.patch(
        f"/knowledge-packs/{pack_id}",
        headers=manager_headers,
        json={"description": "ok"},
    )
    assert updated.status_code == 200

    deleted = client.delete(f"/knowledge-packs/{pack_id}", headers=manager_headers)
    assert deleted.status_code == 403


def test_knowledge_pack_audit_events(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-kp-audit@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Audit Project")
    pack = _create_pack(client, headers, project["id"], "Audited Pack")
    pack_id = pack["id"]

    assert any(
        str(row.entity_id) == pack_id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_KNOWLEDGE_PACK_CREATED)
        )
    )

    client.patch(
        f"/knowledge-packs/{pack_id}",
        headers=headers,
        json={"name": "Audited Pack 2"},
    )
    client.patch(
        f"/knowledge-packs/{pack_id}/sections/facts",
        headers=headers,
        json={"content": "1+1=2"},
    )
    keys = [item.key for item in initial_section_definitions()]
    client.patch(
        f"/knowledge-packs/{pack_id}/sections/reorder",
        headers=headers,
        json=list(reversed(keys)),
    )
    client.delete(f"/knowledge-packs/{pack_id}", headers=headers)

    actions = {
        row.action
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.entity_id == pack_id)
        )
    }
    assert ACTION_KNOWLEDGE_PACK_UPDATED in actions
    assert ACTION_KNOWLEDGE_PACK_SECTION_UPDATED in actions
    assert ACTION_KNOWLEDGE_PACK_SECTIONS_REORDERED in actions
    assert ACTION_KNOWLEDGE_PACK_ARCHIVED in actions

    section_event = next(
        row
        for row in db_session.scalars(
            select(AuditLog).where(
                AuditLog.action == ACTION_KNOWLEDGE_PACK_SECTION_UPDATED
            )
        )
        if str(row.entity_id) == pack_id
    )
    assert section_event.event_metadata["section_key"] == "facts"
