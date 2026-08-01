"""Project management foundation tests."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_CATEGORY_CREATED,
    ACTION_CATEGORY_UPDATED,
    ACTION_PROJECT_ARCHIVED,
    ACTION_PROJECT_CREATED,
    ACTION_PROJECT_MEMBER_ADDED,
    ACTION_PROJECT_MEMBER_REMOVED,
    ACTION_PROJECT_UPDATED,
    ACTION_TAG_CREATED,
    ACTION_TAG_UPDATED,
)
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.models.project import ProjectMember
from app.schemas.auth import UserCreate
from app.schemas.project import (
    CategoryCreate,
    CategoryUpdate,
    ProjectCreate,
    TagCreate,
    TagUpdate,
)
from app.services import project_service, rbac_service
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Project",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-projects@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _writer(db: Session, email: str = "writer-projects@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    writer = rbac_service.get_role_by_name(db, "Script Writer")
    assign_role_to_user(db, user_id=user.id, role_id=writer.id)
    return user


def _create_category(client: TestClient, headers: dict, name: str = "Science"):
    response = client.post(
        "/categories",
        headers=headers,
        json={"name": name, "slug": name.lower()},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_tag(client: TestClient, headers: dict, name: str = "Biology"):
    response = client.post(
        "/tags",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_project_creation_and_code_generation(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    first = client.post("/projects", headers=headers, json={"name": "Alpha"})
    second = client.post("/projects", headers=headers, json={"name": "Beta"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["project_code"].startswith("CRX-")
    assert second.json()["project_code"].startswith("CRX-")
    assert first.json()["project_code"] != second.json()["project_code"]
    assert first.json()["created_by"] == str(owner.id)
    assert first.json()["status"] == "draft"


def test_creator_becomes_member(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    created = client.post("/projects", headers=headers, json={"name": "Member Seed"})
    project_id = created.json()["id"]
    members = client.get(f"/projects/{project_id}/members", headers=headers)
    assert members.status_code == 200
    assert any(item["user_id"] == str(owner.id) for item in members.json())
    row = db_session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == owner.id,
        )
    )
    assert row is not None


def test_project_list_pagination_and_search(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    for index in range(3):
        client.post(
            "/projects",
            headers=headers,
            json={"name": f"Searchable Project {index}"},
        )
    page = client.get("/projects?page=1&page_size=2", headers=headers)
    assert page.status_code == 200
    body = page.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3
    assert len(body["items"]) == 2

    by_name = client.get("/projects?search=Searchable%20Project%201", headers=headers)
    assert by_name.status_code == 200
    assert by_name.json()["total"] >= 1
    code = by_name.json()["items"][0]["project_code"]
    by_code = client.get(f"/projects?search={code}", headers=headers)
    assert by_code.status_code == 200
    assert by_code.json()["total"] >= 1


def test_project_status_category_tag_filters(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    category = _create_category(client, headers, "History")
    tag = _create_tag(client, headers, "Ancient")
    created = client.post(
        "/projects",
        headers=headers,
        json={
            "name": "Filtered Project",
            "status": "active",
            "category_id": category["id"],
            "tag_ids": [tag["id"]],
        },
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    by_status = client.get("/projects?status=active", headers=headers)
    assert any(item["id"] == project_id for item in by_status.json()["items"])

    by_category = client.get(
        f"/projects?category_id={category['id']}",
        headers=headers,
    )
    assert any(item["id"] == project_id for item in by_category.json()["items"])

    by_tag = client.get(f"/projects?tag_id={tag['id']}", headers=headers)
    assert any(item["id"] == project_id for item in by_tag.json()["items"])

    by_creator = client.get(f"/projects?created_by={owner.id}", headers=headers)
    assert any(item["id"] == project_id for item in by_creator.json()["items"])


def test_project_detail_update_and_archive(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    created = client.post(
        "/projects",
        headers=headers,
        json={"name": "Lifecycle", "description": "plain text"},
    )
    project_id = created.json()["id"]

    detail = client.get(f"/projects/{project_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Lifecycle"
    assert "password" not in detail.text.lower()
    assert "token" not in detail.json()

    updated = client.patch(
        f"/projects/{project_id}",
        headers=headers,
        json={"name": "Lifecycle Updated", "status": "active"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Lifecycle Updated"
    assert updated.json()["status"] == "active"

    archived = client.delete(f"/projects/{project_id}", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    # Physical row remains
    still = client.get(f"/projects/{project_id}", headers=headers)
    assert still.status_code == 200
    assert still.json()["status"] == "archived"


def test_unauthorized_project_mutations(
    client: TestClient,
    db_session: Session,
) -> None:
    writer = _writer(db_session, "writer-authz@example.com")
    owner = _owner(db_session, "owner-authz@example.com")
    owner_headers = _auth_header(owner)
    writer_headers = _auth_header(writer)

    denied_create = client.post(
        "/projects",
        headers=writer_headers,
        json={"name": "Nope"},
    )
    assert denied_create.status_code == 403

    created = client.post(
        "/projects",
        headers=owner_headers,
        json={"name": "Protected"},
    )
    project_id = created.json()["id"]

    denied_update = client.patch(
        f"/projects/{project_id}",
        headers=writer_headers,
        json={"name": "Hacked"},
    )
    assert denied_update.status_code == 403

    denied_delete = client.delete(f"/projects/{project_id}", headers=writer_headers)
    assert denied_delete.status_code == 403

    # Script Writer can view
    allowed_view = client.get(f"/projects/{project_id}", headers=writer_headers)
    assert allowed_view.status_code == 200

    unauth = client.get("/projects")
    assert unauth.status_code == 401


def test_project_members_add_remove_and_duplicate(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-members@example.com")
    member_user = _user(db_session, "member@example.com")
    headers = _auth_header(owner)
    created = client.post("/projects", headers=headers, json={"name": "Team"})
    project_id = created.json()["id"]

    added = client.post(
        f"/projects/{project_id}/members/{member_user.id}",
        headers=headers,
    )
    assert added.status_code == 201
    assert added.json()["user_id"] == str(member_user.id)
    assert "password" not in added.text.lower()

    duplicate = client.post(
        f"/projects/{project_id}/members/{member_user.id}",
        headers=headers,
    )
    assert duplicate.status_code == 409

    removed = client.delete(
        f"/projects/{project_id}/members/{member_user.id}",
        headers=headers,
    )
    assert removed.status_code == 200


def test_categories_and_tags(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-taxonomy@example.com")
    headers = _auth_header(owner)

    category = client.post(
        "/categories",
        headers=headers,
        json={"name": "Math", "slug": "math"},
    )
    assert category.status_code == 201
    category_id = category.json()["id"]

    dup_category = client.post(
        "/categories",
        headers=headers,
        json={"name": "Math 2", "slug": "math"},
    )
    assert dup_category.status_code == 409

    patched_category = client.patch(
        f"/categories/{category_id}",
        headers=headers,
        json={"description": "Numbers"},
    )
    assert patched_category.status_code == 200
    assert patched_category.json()["description"] == "Numbers"

    tag = client.post("/tags", headers=headers, json={"name": "Algebra"})
    assert tag.status_code == 201
    tag_id = tag.json()["id"]
    assert tag.json()["slug"] == "algebra"

    dup_tag = client.post("/tags", headers=headers, json={"name": "Algebra"})
    assert dup_tag.status_code == 409

    patched_tag = client.patch(
        f"/tags/{tag_id}",
        headers=headers,
        json={"name": "Algebra Advanced"},
    )
    assert patched_tag.status_code == 200
    assert patched_tag.json()["name"] == "Algebra Advanced"

    project = client.post(
        "/projects",
        headers=headers,
        json={
            "name": "Tagged",
            "category_id": category_id,
            "tag_ids": [tag_id],
        },
    )
    assert project.status_code == 201
    body = project.json()
    assert body["category"]["id"] == category_id
    assert any(item["id"] == tag_id for item in body["tags"])


def test_project_rbac_permissions(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    # Content Manager: view/create/update, no delete
    manager = _user(db_session, "manager@example.com")
    role = rbac_service.get_role_by_name(db_session, "Content Manager")
    assign_role_to_user(db_session, user_id=manager.id, role_id=role.id)
    headers = _auth_header(manager)

    created = client.post("/projects", headers=headers, json={"name": "CM Project"})
    assert created.status_code == 201
    project_id = created.json()["id"]

    updated = client.patch(
        f"/projects/{project_id}",
        headers=headers,
        json={"name": "CM Project 2"},
    )
    assert updated.status_code == 200

    deleted = client.delete(f"/projects/{project_id}", headers=headers)
    assert deleted.status_code == 403


def test_project_audit_events(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-audit-projects@example.com")
    member_user = _user(db_session, "audit-member@example.com")
    headers = _auth_header(owner)

    created = client.post("/projects", headers=headers, json={"name": "Audited"})
    project_id = created.json()["id"]

    created_events = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_PROJECT_CREATED)
    ).all()
    assert any(str(row.entity_id) == project_id for row in created_events)

    client.patch(
        f"/projects/{project_id}",
        headers=headers,
        json={"name": "Audited 2"},
    )
    updated_events = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_PROJECT_UPDATED)
    ).all()
    assert any(str(row.entity_id) == project_id for row in updated_events)
    meta = next(
        row.event_metadata
        for row in updated_events
        if str(row.entity_id) == project_id
    )
    assert "changed_fields" in meta
    assert "name" in meta["changed_fields"]

    client.post(f"/projects/{project_id}/members/{member_user.id}", headers=headers)
    client.delete(f"/projects/{project_id}/members/{member_user.id}", headers=headers)
    client.delete(f"/projects/{project_id}", headers=headers)

    assert any(
        str(row.entity_id) == project_id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_PROJECT_MEMBER_ADDED)
        )
    )
    assert any(
        str(row.entity_id) == project_id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_PROJECT_MEMBER_REMOVED)
        )
    )
    assert any(
        str(row.entity_id) == project_id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_PROJECT_ARCHIVED)
        )
    )


def test_category_tag_audit_and_service_helpers(db_session: Session) -> None:
    owner = _owner(db_session, "service-audit@example.com")
    category = project_service.create_category(
        db_session,
        CategoryCreate(name="Physics", slug="physics"),
        actor_user_id=owner.id,
    )
    tag = project_service.create_tag(
        db_session,
        TagCreate(name="Quantum"),
        actor_user_id=owner.id,
    )
    project = project_service.create_project(
        db_session,
        ProjectCreate(name="Service Project", tag_ids=[tag.id]),
        creator=owner,
    )
    assert project_service.is_project_member(db_session, project.id, owner.id)

    project_service.update_category(
        db_session,
        category.id,
        CategoryUpdate(name="Physics Updated"),
        actor_user_id=owner.id,
    )
    project_service.update_tag(
        db_session,
        tag.id,
        TagUpdate(name="Quantum Updated"),
        actor_user_id=owner.id,
    )

    assert any(
        row.entity_id == category.id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_CATEGORY_CREATED)
        )
    )
    assert any(
        row.entity_id == category.id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_CATEGORY_UPDATED)
        )
    )
    assert any(
        row.entity_id == tag.id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_TAG_CREATED)
        )
    )
    assert any(
        row.entity_id == tag.id
        for row in db_session.scalars(
            select(AuditLog).where(AuditLog.action == ACTION_TAG_UPDATED)
        )
    )


def test_invalid_project_status_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-status@example.com")
    headers = _auth_header(owner)
    response = client.post(
        "/projects",
        headers=headers,
        json={"name": "Bad", "status": "published"},
    )
    assert response.status_code == 422
