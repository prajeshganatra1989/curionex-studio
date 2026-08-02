"""Content production workflow tests (M2I)."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.actions import (
    ACTION_WORKFLOW_ARCHIVED,
    ACTION_WORKFLOW_COMPLETED,
    ACTION_WORKFLOW_CREATED,
    ACTION_WORKFLOW_RETURNED_TO_WORKSPACE,
    ACTION_WORKFLOW_REVIEW_SUBMITTED,
    ACTION_WORKFLOW_STAGE_CHANGED,
    ACTION_WORKFLOW_VERSION_CREATED,
)
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.models.content_version import ContentVersion
from app.models.workflow import ContentWorkflow
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user
from app.workflows.snapshot import build_workspace_snapshot


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Workflow",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str | None = None):
    seed_rbac_catalog(db)
    user = _user(db, email or f"owner-wf-{uuid4().hex[:8]}@example.com")
    rbac_service.assign_owner_role(db, user)
    return user


def _project(client: TestClient, headers: dict, name: str = "WF Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _create_script(
    client: TestClient,
    headers: dict,
    project_id: str,
    title: str = "Main Script",
) -> dict:
    response = client.post(
        f"/projects/{project_id}/scripts",
        headers=headers,
        json={"title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _fill_documents(
    client: TestClient,
    headers: dict,
    script_id: str,
    *,
    brief: str = "Brief body",
    spine: str = "Spine body",
    master: str = "Master body",
) -> None:
    for doc_type, content in (
        ("discovery_brief", brief),
        ("story_spine", spine),
        ("master_script", master),
    ):
        response = client.patch(
            f"/scripts/{script_id}/documents/{doc_type}",
            headers=headers,
            json={"content": content},
        )
        assert response.status_code == 200, response.text


def test_script_creation_creates_workflow(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers)
    script = _create_script(client, headers, project["id"])

    workflow = client.get(f"/scripts/{script['id']}/workflow", headers=headers)
    assert workflow.status_code == 200, workflow.text
    body = workflow.json()
    assert body["script_id"] == script["id"]
    assert body["current_stage"] == "workspace"
    assert body["status"] == "active"
    assert body["active_content_version_id"] is None
    assert body["script"]["script_code"] == script["script_code"]

    row = db_session.scalar(
        select(ContentWorkflow).where(ContentWorkflow.script_id == script["id"])
    )
    assert row is not None
    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_CREATED)
        )
        is not None
    )


def test_one_workflow_per_script_constraint(
    client: TestClient,
    db_session: Session,
) -> None:
    import pytest
    from sqlalchemy.exc import IntegrityError

    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Unique WF")
    script = _create_script(client, headers, project["id"])
    existing = db_session.scalar(
        select(ContentWorkflow).where(ContentWorkflow.script_id == script["id"])
    )
    assert existing is not None
    db_session.add(
        ContentWorkflow(
            script_id=script["id"],
            current_stage="workspace",
            status="active",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_workflow_status_version_distinctions(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Status Distinctions")
    script = _create_script(client, headers, project["id"])
    _fill_documents(client, headers, script["id"])

    # Unrelated project version should not become "latest" for this workflow's project
    other = _project(client, headers, "Other for versions")
    other_version = client.post(
        f"/projects/{other['id']}/content-versions",
        headers=headers,
        json={"title": "Other", "content": "x"},
    )
    assert other_version.status_code == 201

    created = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    )
    assert created.status_code == 201, created.text
    active_id = created.json()["content_version"]["id"]

    # Another project version as "noise" latest within same project
    extra = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={"title": "Manual latest", "content": "manual"},
    )
    assert extra.status_code == 201
    latest_id = extra.json()["id"]

    status = client.get(f"/scripts/{script['id']}/workflow/status", headers=headers)
    assert status.status_code == 200
    body = status.json()
    assert body["stage"] == "versioning"
    assert body["status"] == "active"
    assert body["active_version"]["id"] == active_id
    assert body["latest_version"]["id"] == latest_id
    assert body["approved_version"] is None
    assert body["pending_approval"] is None
    assert body["active_version"]["id"] != body["latest_version"]["id"]


def test_create_version_snapshot_and_transitions(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Snapshot Flow")
    script = _create_script(client, headers, project["id"], title="Snapshot Script")

    # Missing content is fine; documents exist as shells — create-version allowed
    created = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    )
    assert created.status_code == 201, created.text
    version = created.json()["content_version"]
    assert version["status"] == "draft"
    assert created.json()["workflow"]["current_stage"] == "versioning"
    assert created.json()["workflow"]["active_content_version_id"] == version["id"]

    detail = client.get(f"/content-versions/{version['id']}", headers=headers)
    content = detail.json()["content"]
    assert "DISCOVERY BRIEF" in content
    assert "STORY SPINE" in content
    assert "MASTER SCRIPT" in content
    brief_pos = content.index("DISCOVERY BRIEF")
    spine_pos = content.index("STORY SPINE")
    master_pos = content.index("MASTER SCRIPT")
    assert brief_pos < spine_pos < master_pos

    # Determinism: same empty docs → same structure
    from app.models.script import ScriptDocument

    docs = list(
        db_session.scalars(
            select(ScriptDocument).where(ScriptDocument.script_id == script["id"])
        ).all()
    )
    assert build_workspace_snapshot(docs) == content

    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_VERSION_CREATED)
        )
        is not None
    )
    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_STAGE_CHANGED)
        )
        is not None
    )


def test_submit_review_approve_complete(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Approve Flow")
    script = _create_script(client, headers, project["id"])
    _fill_documents(client, headers, script["id"], brief="A", spine="B", master="C")

    created = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    ).json()
    version_id = created["content_version"]["id"]

    # Missing version blocks review if cleared — submit requires active version
    reviewed = client.post(
        f"/scripts/{script['id']}/workflow/submit-review",
        headers=headers,
    )
    assert reviewed.status_code == 201, reviewed.text
    assert reviewed.json()["workflow"]["current_stage"] == "review"
    assert reviewed.json()["content_version"]["status"] == "in_review"
    approval_id = reviewed.json()["approval"]["id"]

    duplicate = client.post(
        f"/scripts/{script['id']}/workflow/submit-review",
        headers=headers,
    )
    assert duplicate.status_code == 422

    dup_approval = client.post(
        f"/content-versions/{version_id}/approval-requests",
        headers=headers,
        json={},
    )
    assert dup_approval.status_code == 409

    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_REVIEW_SUBMITTED)
        )
        is not None
    )

    approved = client.post(
        f"/approvals/{approval_id}/approve",
        headers=headers,
        json={"comment": "Ship it"},
    )
    assert approved.status_code == 200

    workflow = client.get(f"/scripts/{script['id']}/workflow", headers=headers).json()
    assert workflow["current_stage"] == "completed"
    assert workflow["status"] == "completed"

    status = client.get(f"/scripts/{script['id']}/workflow/status", headers=headers).json()
    assert status["approved_version"]["id"] == version_id
    assert status["active_version"]["id"] == version_id

    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_COMPLETED)
        )
        is not None
    )


def test_reject_returns_to_workspace_and_new_version(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Reject Flow")
    script = _create_script(client, headers, project["id"])
    _fill_documents(client, headers, script["id"])

    v1 = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    ).json()["content_version"]
    approval_id = client.post(
        f"/scripts/{script['id']}/workflow/submit-review",
        headers=headers,
    ).json()["approval"]["id"]

    rejected = client.post(
        f"/approvals/{approval_id}/reject",
        headers=headers,
        json={"comment": "Needs work"},
    )
    assert rejected.status_code == 200

    workflow = client.get(f"/scripts/{script['id']}/workflow", headers=headers).json()
    assert workflow["current_stage"] == "workspace"
    assert workflow["status"] == "active"

    # Rejected version immutable
    original = client.get(f"/content-versions/{v1['id']}", headers=headers).json()
    assert original["status"] == "rejected"
    assert original["content"] == client.get(
        f"/content-versions/{v1['id']}", headers=headers
    ).json()["content"]
    assert original["version_number"] == 1

    assert (
        db_session.scalar(
            select(AuditLog).where(
                AuditLog.action == ACTION_WORKFLOW_RETURNED_TO_WORKSPACE
            )
        )
        is not None
    )

    _fill_documents(
        client,
        headers,
        script["id"],
        brief="Revised brief",
        spine="Revised spine",
        master="Revised master",
    )
    v2 = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    ).json()["content_version"]
    assert v2["version_number"] == 2
    assert v2["id"] != v1["id"]
    assert "Revised brief" in client.get(
        f"/content-versions/{v2['id']}", headers=headers
    ).json()["content"]
    # Old rejected content unchanged
    assert "Revised brief" not in client.get(
        f"/content-versions/{v1['id']}", headers=headers
    ).json()["content"]


def test_transitions_archive_and_invalid(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Transition Archive")
    script = _create_script(client, headers, project["id"])

    invalid = client.post(
        f"/scripts/{script['id']}/workflow/transition",
        headers=headers,
        json={"target_stage": "completed"},
    )
    assert invalid.status_code == 422

    # workspace → versioning via transition (docs exist as shells)
    moved = client.post(
        f"/scripts/{script['id']}/workflow/transition",
        headers=headers,
        json={"target_stage": "versioning"},
    )
    assert moved.status_code == 200
    assert moved.json()["current_stage"] == "versioning"

    # versioning → review blocked without version
    blocked = client.post(
        f"/scripts/{script['id']}/workflow/transition",
        headers=headers,
        json={"target_stage": "review"},
    )
    assert blocked.status_code == 422

    archived = client.post(
        f"/scripts/{script['id']}/workflow/archive",
        headers=headers,
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert (
        db_session.scalar(
            select(AuditLog).where(AuditLog.action == ACTION_WORKFLOW_ARCHIVED)
        )
        is not None
    )

    # Cannot mutate archived
    assert (
        client.post(
            f"/scripts/{script['id']}/workflow/create-version",
            headers=headers,
        ).status_code
        == 422
    )


def test_archive_from_workspace_and_review(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Archive Stages")
    script_a = _create_script(client, headers, project["id"], title="A")
    assert (
        client.post(
            f"/scripts/{script_a['id']}/workflow/archive",
            headers=headers,
        ).status_code
        == 200
    )

    script_b = _create_script(client, headers, project["id"], title="B")
    _fill_documents(client, headers, script_b["id"])
    client.post(f"/scripts/{script_b['id']}/workflow/create-version", headers=headers)
    client.post(f"/scripts/{script_b['id']}/workflow/submit-review", headers=headers)
    assert (
        client.post(
            f"/scripts/{script_b['id']}/workflow/archive",
            headers=headers,
        ).json()["status"]
        == "archived"
    )


def test_rbac_and_cross_project_access(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    owner_headers = _auth_header(owner)
    project = _project(client, owner_headers, "RBAC WF")
    script = _create_script(client, owner_headers, project["id"])

    from app.models.rbac import Role

    seed_rbac_catalog(db_session)
    outsider = _user(db_session, f"outsider-wf-{uuid4().hex[:8]}@example.com")
    writer_role = db_session.scalar(select(Role).where(Role.name == "Script Writer"))
    assert writer_role is not None
    assign_role_to_user(db_session, user_id=outsider.id, role_id=writer_role.id)
    outsider_headers = _auth_header(outsider)

    # Not a project member
    assert (
        client.get(
            f"/scripts/{script['id']}/workflow",
            headers=outsider_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/scripts/{script['id']}/workflow/transition",
            headers=outsider_headers,
            json={"target_stage": "versioning"},
        ).status_code
        == 403
    )

    # User without workflows.view
    bare = _user(db_session, f"bare-wf-{uuid4().hex[:8]}@example.com")
    bare_headers = _auth_header(bare)
    assert (
        client.get(
            f"/scripts/{script['id']}/workflow",
            headers=bare_headers,
        ).status_code
        == 403
    )

    # Cross-project: other owner cannot access
    other_owner = _owner(db_session, f"other-owner-wf-{uuid4().hex[:8]}@example.com")
    other_headers = _auth_header(other_owner)
    _project(client, other_headers, "Other Owner Project")
    assert (
        client.get(
            f"/scripts/{script['id']}/workflow",
            headers=other_headers,
        ).status_code
        == 403
    )


def test_approval_without_workflow_still_works(
    client: TestClient,
    db_session: Session,
) -> None:
    """M2G compatibility: approve/reject versions not tied to a workflow."""
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "M2G Compat")
    version = client.post(
        f"/projects/{project['id']}/content-versions",
        headers=headers,
        json={"title": "Standalone", "content": "Body"},
    ).json()
    approval = client.post(
        f"/content-versions/{version['id']}/approval-requests",
        headers=headers,
        json={},
    ).json()
    approved = client.post(
        f"/approvals/{approval['id']}/approve",
        headers=headers,
        json={},
    )
    assert approved.status_code == 200
    assert (
        client.get(f"/content-versions/{version['id']}", headers=headers).json()[
            "status"
        ]
        == "approved"
    )


def test_audit_metadata_excludes_full_content(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Audit Meta")
    script = _create_script(client, headers, project["id"])
    secret = "SECRET_FULL_SCRIPT_BODY_SHOULD_NOT_APPEAR"
    _fill_documents(
        client,
        headers,
        script["id"],
        brief=secret,
        spine=secret,
        master=secret,
    )
    client.post(f"/scripts/{script['id']}/workflow/create-version", headers=headers)
    client.post(f"/scripts/{script['id']}/workflow/submit-review", headers=headers)

    logs = list(
        db_session.scalars(
            select(AuditLog).where(
                AuditLog.action.in_(
                    [
                        ACTION_WORKFLOW_VERSION_CREATED,
                        ACTION_WORKFLOW_REVIEW_SUBMITTED,
                        ACTION_WORKFLOW_STAGE_CHANGED,
                    ]
                )
            )
        ).all()
    )
    assert logs
    for log in logs:
        assert secret not in str(log.event_metadata)


def test_version_numbering_with_workflow_versions(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project = _project(client, headers, "Numbering")
    script = _create_script(client, headers, project["id"])
    _fill_documents(client, headers, script["id"])
    v1 = client.post(
        f"/scripts/{script['id']}/workflow/create-version", headers=headers
    ).json()["content_version"]
    assert v1["version_number"] == 1
    # Reject path to create second
    approval = client.post(
        f"/scripts/{script['id']}/workflow/submit-review", headers=headers
    ).json()["approval"]["id"]
    client.post(
        f"/approvals/{approval}/reject",
        headers=headers,
        json={"comment": "Needs a stronger hook"},
    )
    v2 = client.post(
        f"/scripts/{script['id']}/workflow/create-version", headers=headers
    ).json()["content_version"]
    assert v2["version_number"] == 2
    versions = list(
        db_session.scalars(
            select(ContentVersion)
            .where(ContentVersion.project_id == project["id"])
            .order_by(ContentVersion.version_number)
        ).all()
    )
    assert [v.version_number for v in versions] == [1, 2]
