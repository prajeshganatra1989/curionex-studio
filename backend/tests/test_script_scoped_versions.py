"""Script-scoped ContentVersion and approvals inbox tests."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.content_version import ContentVersion
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.rbac_service import seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Script",
            last_name="Version",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-script-cv@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _project(client: TestClient, headers: dict, name: str = "Script CV Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _script(client: TestClient, headers: dict, project_id: str, title: str = "S1") -> dict:
    response = client.post(
        f"/projects/{project_id}/scripts",
        headers=headers,
        json={"title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _fill_docs(client: TestClient, headers: dict, script_id: str) -> None:
    for doc_type, body in (
        ("discovery_brief", "Audience and takeaway for the Short."),
        ("story_spine", "Hook mystery explanation twist ending."),
        ("master_script", "Spoken narration for the Short about the topic."),
    ):
        response = client.patch(
            f"/scripts/{script_id}/documents/{doc_type}",
            headers=headers,
            json={"content": body},
        )
        assert response.status_code == 200, response.text


def test_workflow_created_version_stores_script_id(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers)
    script = _script(client, headers, project["id"])
    _fill_docs(client, headers, script["id"])

    created = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    )
    assert created.status_code == 201, created.text
    version = created.json()["content_version"]
    detail = client.get(f"/content-versions/{version['id']}", headers=headers).json()
    assert detail["script_id"] == script["id"]
    assert detail["project_id"] == project["id"]

    row = db_session.get(ContentVersion, version["id"])
    assert row is not None
    assert str(row.script_id) == script["id"]


def test_cross_project_script_association_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cross-cv@example.com")
    headers = _auth_header(owner)
    project_a = _project(client, headers, "Project A")
    project_b = _project(client, headers, "Project B")
    script_b = _script(client, headers, project_b["id"], "Other Script")

    response = client.post(
        f"/projects/{project_a['id']}/content-versions",
        headers=headers,
        json={
            "title": "Bad link",
            "content": "Body",
            "script_id": script_b["id"],
        },
    )
    assert response.status_code == 422
    assert "same project" in response.json()["detail"].lower()


def test_new_version_from_existing_preserves_script_id(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-preserve-cv@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Preserve")
    script = _script(client, headers, project["id"])
    created = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={
            "title": "Linked",
            "content": "Snapshot",
            "script_id": script["id"],
        },
    )
    assert created.status_code == 201, created.text
    source = created.json()
    assert source["script_id"] == script["id"]

    newer = client.post(
        f"/content-versions/{source['id']}/new-version",
        headers=headers,
    )
    assert newer.status_code == 201, newer.text
    assert newer.json()["script_id"] == script["id"]
    assert newer.json()["content"] == source["content"]
    assert newer.json()["version_number"] == source["version_number"] + 1


def test_script_scoped_list_latest_approved_and_exclusion(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-scope-cv@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Scoped")
    script_a = _script(client, headers, project["id"], "Alpha")
    script_b = _script(client, headers, project["id"], "Beta")

    a1 = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={"title": "A1", "content": "a", "script_id": script_a["id"]},
    ).json()
    client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={"title": "B1", "content": "b", "script_id": script_b["id"]},
    )
    # Project-only historical version
    orphan = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={"title": "Orphan", "content": "o"},
    ).json()
    assert orphan["script_id"] is None

    listed = client.get(
        f"/scripts/{script_a['id']}/content-versions",
        headers=headers,
    )
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert listed.json()["total"] == 1
    assert items[0]["id"] == a1["id"]
    assert all(item["script_id"] == script_a["id"] for item in items)

    latest = client.get(
        f"/scripts/{script_a['id']}/content-versions/latest",
        headers=headers,
    )
    assert latest.status_code == 200
    assert latest.json()["id"] == a1["id"]

    # Approve A1 via approval flow
    req = client.post(
        f"/content-versions/{a1['id']}/approval-requests",
        headers=headers,
        json={},
    )
    approval_id = req.json()["id"]
    client.post(
        f"/approvals/{approval_id}/approve",
        headers=headers,
        json={"comment": "Ship it"},
    )
    approved = client.get(
        f"/scripts/{script_a['id']}/content-versions/approved",
        headers=headers,
    )
    assert approved.status_code == 200
    assert approved.json()["id"] == a1["id"]
    assert approved.json()["status"] == "approved"

    other_list = client.get(
        f"/scripts/{script_b['id']}/content-versions",
        headers=headers,
    ).json()["items"]
    assert a1["id"] not in {item["id"] for item in other_list}


def test_approvals_inbox_and_detail(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-inbox@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Inbox")
    script = _script(client, headers, project["id"])
    version = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={
            "title": f"{script['script_code']} — Inbox",
            "content": "DISCOVERY BRIEF\n\nx\n\nSTORY SPINE\n\ny\n\nMASTER SCRIPT\n\nz\n",
            "script_id": script["id"],
        },
    ).json()
    req = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={},
    )
    approval_id = req.json()["id"]

    inbox = client.get("/approvals", headers=headers, params={"status": "pending"})
    assert inbox.status_code == 200, inbox.text
    assert inbox.json()["total"] >= 1
    match = next(item for item in inbox.json()["items"] if item["id"] == approval_id)
    assert match["project"]["project_code"] == project["project_code"]
    assert match["script"]["script_code"] == script["script_code"]
    assert match["content_version"]["version_number"] == version["version_number"]
    assert "content" not in match["content_version"]

    detail = client.get(f"/approvals/{approval_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["content_version"]["content"].startswith("DISCOVERY BRIEF")
    assert body["script"]["id"] == script["id"]

    rejected = client.post(
        f"/approvals/{approval_id}/reject",
        headers=headers,
        json={},
    )
    assert rejected.status_code == 422

    rejected = client.post(
        f"/approvals/{approval_id}/reject",
        headers=headers,
        json={"comment": "Rewrite the ending"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["comment"] == "Rewrite the ending"


def test_unknown_script_versions_404(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-missing-script@example.com")
    headers = _auth_header(owner)
    response = client.get(
        f"/scripts/{uuid4()}/content-versions",
        headers=headers,
    )
    assert response.status_code == 404
