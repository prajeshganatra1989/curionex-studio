"""Content version and approval tests."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.audit.actions import (
    ACTION_APPROVAL_APPROVED,
    ACTION_APPROVAL_REQUESTED,
    ACTION_CONTENT_VERSION_CREATED,
)
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.models.content_version import ContentVersion
from app.schemas.auth import UserCreate
from app.schemas.content_version import ApprovalRequestCreate, ContentVersionCreate
from app.schemas.project import ProjectCreate
from app.services import content_version_service, rbac_service
from app.services.project_service import create_project
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Version",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-cv@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _project(client: TestClient, headers: dict, name: str = "CV Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _create_version(
    client: TestClient,
    headers: dict,
    project_id: str,
    title: str = "Draft Title",
    content: str = "Snapshot body",
) -> dict:
    response = client.post(
        f"/projects/{project_id}/content-versions",
        headers=headers,
        json={"title": title, "content": content},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_version_numbering_and_snapshots(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers)
    other = _project(client, headers, "Other Project")

    v1 = _create_version(client, headers, project["id"], title="One", content="A")
    v2 = _create_version(client, headers, project["id"], title="Two", content="B")
    o1 = _create_version(client, headers, other["id"], title="Other", content="C")

    assert v1["version_number"] == 1
    assert v2["version_number"] == 2
    assert o1["version_number"] == 1
    assert v1["status"] == "draft"
    assert v1["created_by"] == str(owner.id)
    assert v1["content"] == "A"
    assert v2["title"] == "Two"

    branched = client.post(
        f"/content-versions/{v1['id']}/new-version",
        headers=headers,
    )
    assert branched.status_code == 201
    assert branched.json()["version_number"] == 3
    assert branched.json()["title"] == "One"
    assert branched.json()["content"] == "A"
    assert branched.json()["status"] == "draft"

    original = client.get(f"/content-versions/{v1['id']}", headers=headers)
    assert original.json()["title"] == "One"
    assert original.json()["content"] == "A"
    assert original.json()["version_number"] == 1


def test_list_latest_approved_and_no_mutation_route(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cv-list@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "List CV")
    for index in range(3):
        _create_version(
            client,
            headers,
            project["id"],
            title=f"T{index}",
            content=f"C{index}",
        )

    listed = client.get(
        f"/projects/{project['id']}/content-versions?page=1&page_size=2",
        headers=headers,
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
    assert body["items"][0]["version_number"] > body["items"][1]["version_number"]

    latest = client.get(
        f"/projects/{project['id']}/content-versions/latest",
        headers=headers,
    )
    assert latest.status_code == 200
    assert latest.json()["version_number"] == 3

    assert (
        client.get(
            f"/projects/{project['id']}/content-versions/approved",
            headers=headers,
        ).status_code
        == 404
    )

    assert (
        client.patch(
            f"/content-versions/{latest.json()['id']}",
            headers=headers,
            json={"title": "Hacked"},
        ).status_code
        == 405
    )


def test_approval_lifecycle_and_no_transfer(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cv-approval@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Approval Project")
    version = _create_version(client, headers, project["id"], content="Body V1")

    requested = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={"comment": "Please review"},
    )
    assert requested.status_code == 201
    approval_id = requested.json()["id"]
    assert requested.json()["status"] == "pending"

    detail = client.get(f"/content-versions/{version['id']}", headers=headers)
    assert detail.json()["status"] == "in_review"

    duplicate = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={},
    )
    assert duplicate.status_code == 409

    approved = client.post(
        f"/approvals/{approval_id}/approve",
        headers=headers,
        json={"comment": "Looks good"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_by"] == str(owner.id)
    assert approved.json()["reviewed_at"] is not None
    assert approved.json()["comment"] == "Looks good"

    version_after = client.get(f"/content-versions/{version['id']}", headers=headers)
    assert version_after.json()["status"] == "approved"

    again = client.post(
        f"/approvals/{approval_id}/approve",
        headers=headers,
        json={},
    )
    assert again.status_code == 409

    approved_latest = client.get(
        f"/projects/{project['id']}/content-versions/approved",
        headers=headers,
    )
    assert approved_latest.status_code == 200
    assert approved_latest.json()["id"] == version["id"]

    v2 = client.post(
        f"/content-versions/{version['id']}/new-version",
        headers=headers,
    )
    assert v2.status_code == 201
    assert v2.json()["status"] == "draft"
    assert v2.json()["version_number"] == 2
    history = client.get(
        f"/content-versions/{v2.json()['id']}/approvals",
        headers=headers,
    )
    assert history.status_code == 200
    assert history.json() == []

    old_history = client.get(
        f"/content-versions/{version['id']}/approvals",
        headers=headers,
    )
    assert len(old_history.json()) == 1
    assert old_history.json()[0]["status"] == "approved"


def test_reject_and_cancel_flow(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cv-reject@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Reject Project")
    version = _create_version(client, headers, project["id"])

    req = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={},
    )
    approval_id = req.json()["id"]
    rejected = client.post(
        f"/approvals/{approval_id}/reject",
        headers=headers,
        json={"comment": "Needs work"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert (
        client.get(f"/content-versions/{version['id']}", headers=headers).json()[
            "status"
        ]
        == "rejected"
    )

    newer = client.post(
        f"/content-versions/{version['id']}/new-version",
        headers=headers,
    )
    assert newer.json()["status"] == "draft"

    pending = client.post(
        f"/content-versions/{newer.json()['id']}/approval-requests",
        headers=headers,
        json={},
    )
    cancelled = client.post(
        f"/approvals/{pending.json()['id']}/cancel",
        headers=headers,
        json={"comment": "Withdrawn"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert (
        client.get(
            f"/content-versions/{newer.json()['id']}",
            headers=headers,
        ).json()["status"]
        == "draft"
    )


def test_rbac_and_project_access(
    client: TestClient,
    db_session: Session,
) -> None:
    seed_rbac_catalog(db_session)
    writer = _user(db_session, "writer-cv@example.com")
    writer_role = rbac_service.get_role_by_name(db_session, "Script Writer")
    assign_role_to_user(db_session, user_id=writer.id, role_id=writer_role.id)

    reviewer = _user(db_session, "reviewer-cv@example.com")
    reviewer_role = rbac_service.get_role_by_name(db_session, "Reviewer")
    assign_role_to_user(db_session, user_id=reviewer.id, role_id=reviewer_role.id)

    owner = _owner(db_session, "owner-cv-rbac@example.com")
    owner_headers = _auth_header(owner)
    writer_headers = _auth_header(writer)
    reviewer_headers = _auth_header(reviewer)

    project = _project(client, owner_headers, "RBAC CV")
    client.post(
        f"/projects/{project['id']}/members/{writer.id}",
        headers=owner_headers,
    )
    client.post(
        f"/projects/{project['id']}/members/{reviewer.id}",
        headers=owner_headers,
    )

    created = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=writer_headers,
        json={"title": "W", "content": "body"},
    )
    assert created.status_code == 201
    version_id = created.json()["id"]

    assert (
        client.post(
            f"/projects/{project['id']}/content-versions",
            headers=reviewer_headers,
            json={"title": "Nope", "content": "x"},
        ).status_code
        == 403
    )

    req = client.post(
        f"/content-versions/{version_id}/approval-requests",
        headers=writer_headers,
        json={},
    )
    assert req.status_code == 201

    assert (
        client.post(
            f"/approvals/{req.json()['id']}/approve",
            headers=writer_headers,
            json={},
        ).status_code
        == 403
    )

    assert (
        client.post(
            f"/approvals/{req.json()['id']}/approve",
            headers=reviewer_headers,
            json={},
        ).status_code
        == 200
    )

    outsider = _owner(db_session, "outsider-cv@example.com")
    assert (
        client.get(
            f"/content-versions/{version_id}",
            headers=_auth_header(outsider),
        ).status_code
        == 403
    )
    assert client.get(f"/content-versions/{version_id}").status_code == 401


def test_audit_events_without_content_snapshot(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cv-audit@example.com")
    headers = _auth_header(owner)
    project = _project(client, headers, "Audit CV")
    version = _create_version(
        client,
        headers,
        project["id"],
        content="SECRET_SNAPSHOT_SHOULD_NOT_APPEAR",
    )
    req = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={},
    )
    client.post(
        f"/approvals/{req.json()['id']}/approve",
        headers=headers,
        json={},
    )

    events = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.action.in_(
                    [
                        ACTION_CONTENT_VERSION_CREATED,
                        ACTION_APPROVAL_REQUESTED,
                        ACTION_APPROVAL_APPROVED,
                    ]
                )
            )
        )
    )
    assert any(row.action == ACTION_CONTENT_VERSION_CREATED for row in events)
    assert any(row.action == ACTION_APPROVAL_REQUESTED for row in events)
    assert any(row.action == ACTION_APPROVAL_APPROVED for row in events)
    for row in events:
        meta = row.event_metadata or {}
        assert "SECRET_SNAPSHOT_SHOULD_NOT_APPEAR" not in str(meta)
        assert "content" not in meta
        assert "password" not in meta
        assert "token" not in meta


def test_pending_uniqueness_and_version_unique_constraint(
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cv-constraints@example.com")
    project = create_project(
        db_session,
        ProjectCreate(name="Constraint Project"),
        creator=owner,
    )
    v1 = content_version_service.create_content_version(
        db_session,
        project.id,
        ContentVersionCreate(title="T", content="C"),
        creator=owner,
    )
    content_version_service.request_approval(
        db_session,
        v1.id,
        ApprovalRequestCreate(),
        requester=owner,
    )
    with pytest.raises(content_version_service.ConflictError):
        content_version_service.request_approval(
            db_session,
            v1.id,
            ApprovalRequestCreate(),
            requester=owner,
        )

    dup = ContentVersion(
        project_id=project.id,
        version_number=1,
        status="draft",
        title="Dup",
        content="x",
        created_by=owner.id,
    )
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_concurrent_version_allocation(engine) -> None:
    """Two connections allocate distinct version numbers under advisory locks."""
    from sqlalchemy import text

    from app.models.user import User

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup = SessionLocal()
    project_id = None
    creator_id = None
    try:
        owner = _owner(setup, "owner-cv-concurrent@example.com")
        project = create_project(
            setup,
            ProjectCreate(name="Concurrent Project"),
            creator=owner,
        )
        project_id = project.id
        creator_id = owner.id
    finally:
        setup.close()

    results: list[int] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(2)

    def worker() -> None:
        session = SessionLocal()
        try:
            barrier.wait(timeout=5)
            creator = session.get(User, creator_id)
            assert creator is not None
            version = content_version_service.create_content_version(
                session,
                project_id,
                ContentVersionCreate(title="Concurrent", content="body"),
                creator=creator,
            )
            results.append(version.version_number)
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
    assert sorted(results) == [1, 2]

    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM content_versions WHERE project_id = :pid"),
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


