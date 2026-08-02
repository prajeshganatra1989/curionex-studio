"""Production Mode API tests — overview, queue, settings, RBAC, membership."""

from __future__ import annotations

from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.credentials import reset_fernet_cache
from app.audit.actions import ACTION_PRODUCTION_SETTINGS_UPDATED
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.audit import AuditLog
from app.models.production import ProductionSettings
from app.production.stages import (
    DEFAULT_APPROVED_TARGET,
    DEFAULT_DAILY_TARGET,
    DEFAULT_WEEKLY_TARGET,
    PRODUCTION_STAGES,
)
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
            first_name="Prod",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str | None = None):
    seed_rbac_catalog(db)
    user = _user(db, email or f"owner-prod-{uuid4().hex[:8]}@example.com")
    rbac_service.assign_owner_role(db, user)
    return user


def _role_user(db: Session, email: str, role_name: str):
    seed_rbac_catalog(db)
    user = _user(db, email)
    role = rbac_service.get_role_by_name(db, role_name)
    assert role is not None
    assign_role_to_user(db, user_id=user.id, role_id=role.id)
    return user


def _enable_credentials_key(monkeypatch) -> str:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("AI_CREDENTIALS_KEY", key)
    get_settings.cache_clear()
    reset_fernet_cache()
    return key


def _setup_openai(client: TestClient, headers: dict) -> str:
    providers = client.get("/ai/providers", headers=headers).json()
    openai = next(p for p in providers if p["code"] == "openai")
    cred = client.post(
        f"/ai/providers/{openai['id']}/credentials",
        headers=headers,
        json={"api_key": "sk-test-not-real"},
    )
    assert cred.status_code == 200, cred.text
    models = client.get(
        f"/ai/models?provider_id={openai['id']}", headers=headers
    ).json()
    return models[0]["id"]


def _project(client: TestClient, headers: dict, name: str = "Prod Project") -> dict:
    response = client.post("/projects", headers=headers, json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _create_script(
    client: TestClient,
    headers: dict,
    project_id: str,
    title: str = "Main Script",
    *,
    knowledge_pack_id: str | None = None,
) -> dict:
    payload: dict = {"title": title}
    if knowledge_pack_id:
        payload["knowledge_pack_id"] = knowledge_pack_id
    response = client.post(
        f"/projects/{project_id}/scripts",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_pack(
    client: TestClient, headers: dict, project_id: str, name: str = "Research Pack"
) -> dict:
    response = client.post(
        f"/projects/{project_id}/knowledge-packs",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _put_document(
    client: TestClient,
    headers: dict,
    script_id: str,
    document_type: str,
    content: str,
) -> None:
    response = client.patch(
        f"/scripts/{script_id}/documents/{document_type}",
        headers=headers,
        json={"content": content},
    )
    assert response.status_code == 200, response.text


def _fill_documents(
    client: TestClient,
    headers: dict,
    script_id: str,
    *,
    brief: str = "Brief body",
    spine: str = "Spine body",
    master: str = "Master body",
) -> None:
    _put_document(client, headers, script_id, "discovery_brief", brief)
    _put_document(client, headers, script_id, "story_spine", spine)
    _put_document(client, headers, script_id, "master_script", master)


# --- Settings ---


def test_settings_defaults_and_patch_audit(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)

    get_resp = client.get("/production/settings", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    body = get_resp.json()
    assert body["approved_script_target"] == DEFAULT_APPROVED_TARGET
    assert body["daily_approved_script_target"] == DEFAULT_DAILY_TARGET
    assert body["weekly_approved_script_target"] == DEFAULT_WEEKLY_TARGET
    assert body["updated_by"] is None

    row = db_session.scalar(select(ProductionSettings).limit(1))
    assert row is not None

    patched = client.patch(
        "/production/settings",
        headers=headers,
        json={
            "approved_script_target": 150,
            "daily_approved_script_target": 3,
            "weekly_approved_script_target": 20,
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["approved_script_target"] == 150
    assert patched.json()["daily_approved_script_target"] == 3
    assert patched.json()["weekly_approved_script_target"] == 20
    assert patched.json()["updated_by"] == str(owner.id)

    audit = db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == ACTION_PRODUCTION_SETTINGS_UPDATED
        )
    )
    assert audit is not None
    assert audit.actor_user_id == owner.id
    meta = audit.event_metadata or {}
    assert "changed_fields" in meta
    assert meta["changed_fields"]["approved_script_target"]["old"] == DEFAULT_APPROVED_TARGET
    assert meta["changed_fields"]["approved_script_target"]["new"] == 150


def test_settings_patch_validation(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    client.get("/production/settings", headers=headers)

    empty = client.patch("/production/settings", headers=headers, json={})
    assert empty.status_code == 422, empty.text

    too_low = client.patch(
        "/production/settings",
        headers=headers,
        json={"approved_script_target": 0},
    )
    assert too_low.status_code == 422

    too_high = client.patch(
        "/production/settings",
        headers=headers,
        json={"daily_approved_script_target": 101},
    )
    assert too_high.status_code == 422


# --- Overview ---


def test_overview_goals_stage_counts_ai_quality(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session)
    headers = _auth_header(owner)
    _setup_openai(client, headers)

    # Project without script → idea (overview includes project-only units).
    _project(client, headers, "Idea Only")

    # Pack + script, no docs → discovery_brief
    p1 = _project(client, headers, "Discovery Project")
    pack1 = _create_pack(client, headers, p1["id"])
    _create_script(
        client, headers, p1["id"], "Discovery Script", knowledge_pack_id=pack1["id"]
    )

    # Brief only → story_spine
    p2 = _project(client, headers, "Spine Project")
    pack2 = _create_pack(client, headers, p2["id"])
    s2 = _create_script(
        client, headers, p2["id"], "Spine Script", knowledge_pack_id=pack2["id"]
    )
    _put_document(client, headers, s2["id"], "discovery_brief", "Brief content")

    # Brief + spine → master_script
    p3 = _project(client, headers, "Master Project")
    pack3 = _create_pack(client, headers, p3["id"])
    s3 = _create_script(
        client, headers, p3["id"], "Master Script", knowledge_pack_id=pack3["id"]
    )
    _put_document(client, headers, s3["id"], "discovery_brief", "Brief")
    _put_document(client, headers, s3["id"], "story_spine", "Spine")

    # Full docs → quality_review
    p4 = _project(client, headers, "Quality Project")
    pack4 = _create_pack(client, headers, p4["id"])
    s4 = _create_script(
        client, headers, p4["id"], "Quality Script", knowledge_pack_id=pack4["id"]
    )
    _fill_documents(client, headers, s4["id"])

    overview = client.get("/production/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    body = overview.json()

    goals = body["goals"]
    assert goals["approved_target"] == DEFAULT_APPROVED_TARGET
    assert goals["approved_total"] == 0
    assert goals["remaining"] == DEFAULT_APPROVED_TARGET
    assert goals["completion_percent"] == 0.0
    assert goals["daily_target"] == DEFAULT_DAILY_TARGET
    assert goals["weekly_target"] == DEFAULT_WEEKLY_TARGET
    assert goals["approved_today"] == 0
    assert goals["approved_this_week"] == 0

    counts = body["stage_counts"]
    assert set(counts.keys()) == set(PRODUCTION_STAGES)
    assert counts["idea"] >= 1
    assert counts["discovery_brief"] >= 1
    assert counts["story_spine"] >= 1
    assert counts["master_script"] >= 1
    assert counts["quality_review"] >= 1

    ai = body["ai"]
    assert ai["queued"] == 0
    assert ai["running"] == 0
    assert ai["failed"] == 0
    assert ai["completed_today"] == 0
    assert ai["estimated_cost_today"] == 0.0

    quality = body["quality"]
    assert quality["average_current_score"] is None
    assert quality["scripts_needing_revision"] == 0
    assert quality["stale_reviews"] == 0
    assert quality["high_risk_fact_flags"] == 0


# --- Queue ---


def test_queue_pagination_search_stage_filter(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session)
    headers = _auth_header(owner)
    _setup_openai(client, headers)

    project = _project(client, headers, "Queue Search Project")
    pack = _create_pack(client, headers, project["id"])

    scripts = []
    for i in range(5):
        script = _create_script(
            client,
            headers,
            project["id"],
            f"Alpha Script {i}" if i < 3 else f"Beta Script {i}",
            knowledge_pack_id=pack["id"],
        )
        scripts.append(script)
        if i == 0:
            _fill_documents(client, headers, script["id"])
        elif i == 1:
            _put_document(
                client, headers, script["id"], "discovery_brief", "Brief only"
            )

    page1 = client.get(
        "/production/queue",
        headers=headers,
        params={"page": 1, "page_size": 2},
    )
    assert page1.status_code == 200, page1.text
    assert page1.json()["page"] == 1
    assert page1.json()["page_size"] == 2
    assert page1.json()["total"] >= 5
    assert len(page1.json()["items"]) == 2

    page2 = client.get(
        "/production/queue",
        headers=headers,
        params={"page": 2, "page_size": 2},
    )
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 2
    ids_p1 = {item["script_id"] for item in page1.json()["items"]}
    ids_p2 = {item["script_id"] for item in page2.json()["items"]}
    assert ids_p1.isdisjoint(ids_p2)

    search = client.get(
        "/production/queue",
        headers=headers,
        params={"search": "Alpha"},
    )
    assert search.status_code == 200
    assert search.json()["total"] >= 3
    for item in search.json()["items"]:
        assert "Alpha" in (item["script_title"] or "")

    stage_filter = client.get(
        "/production/queue",
        headers=headers,
        params={"production_stage": "quality_review"},
    )
    assert stage_filter.status_code == 200
    assert stage_filter.json()["total"] >= 1
    for item in stage_filter.json()["items"]:
        assert item["production_stage"] == "quality_review"

    invalid_stage = client.get(
        "/production/queue",
        headers=headers,
        params={"production_stage": "not_a_stage"},
    )
    assert invalid_stage.status_code == 422


def test_queue_next_action_codes_and_no_document_bodies(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session)
    headers = _auth_header(owner)
    _setup_openai(client, headers)

    project = _project(client, headers, "Next Action Project")
    pack = _create_pack(client, headers, project["id"])

    discovery = _create_script(
        client, headers, project["id"], "Needs Brief", knowledge_pack_id=pack["id"]
    )

    spine = _create_script(
        client, headers, project["id"], "Needs Spine", knowledge_pack_id=pack["id"]
    )
    _put_document(client, headers, spine["id"], "discovery_brief", "Brief body")

    master = _create_script(
        client, headers, project["id"], "Needs Master", knowledge_pack_id=pack["id"]
    )
    _put_document(client, headers, master["id"], "discovery_brief", "Brief")
    _put_document(client, headers, master["id"], "story_spine", "Spine")

    quality = _create_script(
        client, headers, project["id"], "Needs Quality", knowledge_pack_id=pack["id"]
    )
    _fill_documents(client, headers, quality["id"], master="SECRET MASTER BODY XYZ")

    queue = client.get("/production/queue", headers=headers)
    assert queue.status_code == 200, queue.text
    items = {item["script_id"]: item for item in queue.json()["items"]}

    assert items[discovery["id"]]["production_stage"] == "discovery_brief"
    assert items[discovery["id"]]["next_action"]["code"] == "generate_discovery_brief"

    assert items[spine["id"]]["production_stage"] == "story_spine"
    assert items[spine["id"]]["next_action"]["code"] == "generate_story_spine"

    assert items[master["id"]]["production_stage"] == "master_script"
    assert items[master["id"]]["next_action"]["code"] == "generate_master_script"

    assert items[quality["id"]]["production_stage"] == "quality_review"
    assert items[quality["id"]]["next_action"]["code"] == "run_quality_review"

    # Document statuses only — never raw bodies.
    quality_item = items[quality["id"]]
    assert set(quality_item["documents"].keys()) == {
        "discovery_brief",
        "story_spine",
        "master_script",
    }
    assert quality_item["documents"]["master_script"] == "complete"
    raw = queue.text
    assert "SECRET MASTER BODY XYZ" not in raw
    assert "content" not in quality_item["documents"]
    assert "body" not in quality_item


def test_queue_membership_isolation(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner_a = _owner(db_session, f"owner-a-{uuid4().hex[:8]}@example.com")
    owner_b = _owner(db_session, f"owner-b-{uuid4().hex[:8]}@example.com")
    headers_a = _auth_header(owner_a)
    headers_b = _auth_header(owner_b)
    _setup_openai(client, headers_a)
    _setup_openai(client, headers_b)

    project_a = _project(client, headers_a, "Owner A Project")
    pack_a = _create_pack(client, headers_a, project_a["id"])
    script_a = _create_script(
        client,
        headers_a,
        project_a["id"],
        "Owner A Script Unique",
        knowledge_pack_id=pack_a["id"],
    )

    project_b = _project(client, headers_b, "Owner B Project")
    pack_b = _create_pack(client, headers_b, project_b["id"])
    script_b = _create_script(
        client,
        headers_b,
        project_b["id"],
        "Owner B Script Unique",
        knowledge_pack_id=pack_b["id"],
    )

    queue_a = client.get("/production/queue", headers=headers_a)
    assert queue_a.status_code == 200
    ids_a = {item["script_id"] for item in queue_a.json()["items"]}
    assert script_a["id"] in ids_a
    assert script_b["id"] not in ids_a

    queue_b = client.get("/production/queue", headers=headers_b)
    assert queue_b.status_code == 200
    ids_b = {item["script_id"] for item in queue_b.json()["items"]}
    assert script_b["id"] in ids_b
    assert script_a["id"] not in ids_b

    overview_a = client.get("/production/overview", headers=headers_a).json()
    overview_b = client.get("/production/overview", headers=headers_b).json()
    # Each owner sees at least their own discovery_brief script.
    assert overview_a["stage_counts"]["discovery_brief"] >= 1
    assert overview_b["stage_counts"]["discovery_brief"] >= 1


def test_queue_version_and_review_next_actions(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session)
    headers = _auth_header(owner)
    _setup_openai(client, headers)

    project = _project(client, headers, "Version Flow Project")
    pack = _create_pack(client, headers, project["id"])
    script = _create_script(
        client, headers, project["id"], "Version Script", knowledge_pack_id=pack["id"]
    )
    _fill_documents(client, headers, script["id"])

    # Create workflow version → version_created (draft, no pending approval).
    created = client.post(
        f"/scripts/{script['id']}/workflow/create-version",
        headers=headers,
    )
    assert created.status_code == 201, created.text

    queue = client.get("/production/queue", headers=headers)
    item = next(
        i for i in queue.json()["items"] if i["script_id"] == script["id"]
    )
    assert item["production_stage"] == "version_created"
    assert item["next_action"]["code"] == "submit_human_review"

    submit = client.post(
        f"/scripts/{script['id']}/workflow/submit-review",
        headers=headers,
    )
    assert submit.status_code == 201, submit.text

    queue2 = client.get("/production/queue", headers=headers)
    item2 = next(
        i for i in queue2.json()["items"] if i["script_id"] == script["id"]
    )
    assert item2["production_stage"] == "pending_human_review"
    assert item2["next_action"]["code"] in {
        "review_approval",
        "open_pending_review",
    }


# --- RBAC ---


def test_production_rbac_reviewer_view_cannot_manage(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    owner_headers = _auth_header(owner)
    project = _project(client, owner_headers, "RBAC Prod Project")

    reviewer = _role_user(
        db_session, f"reviewer-prod-{uuid4().hex[:8]}@example.com", "Reviewer"
    )
    member = client.post(
        f"/projects/{project['id']}/members/{reviewer.id}",
        headers=owner_headers,
    )
    assert member.status_code == 201, member.text

    reviewer_headers = _auth_header(reviewer)

    assert client.get("/production/overview", headers=reviewer_headers).status_code == 200
    assert client.get("/production/queue", headers=reviewer_headers).status_code == 200
    assert client.get("/production/metrics", headers=reviewer_headers).status_code == 200
    assert client.get("/production/settings", headers=reviewer_headers).status_code == 200
    assert client.get("/production/activity", headers=reviewer_headers).status_code == 200

    patch = client.patch(
        "/production/settings",
        headers=reviewer_headers,
        json={"approved_script_target": 200},
    )
    assert patch.status_code == 403

    bare = _user(db_session, f"bare-prod-{uuid4().hex[:8]}@example.com")
    bare_headers = _auth_header(bare)
    assert client.get("/production/overview", headers=bare_headers).status_code == 403
    assert client.get("/production/queue", headers=bare_headers).status_code == 403


def test_metrics_ranges(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    _project(client, headers, "Metrics Project")

    for range_key in ("today", "7d", "30d"):
        resp = client.get(
            "/production/metrics",
            headers=headers,
            params={"range": range_key},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["range"] == range_key
        assert body["scripts_approved"] == 0
        assert body["versions_created"] == 0
        assert body["quality_reviews_completed"] == 0
        assert body["average_quality_score"] is None
        assert body["ai_jobs_completed"] == 0
        assert body["ai_jobs_failed"] == 0
        assert body["estimated_ai_cost"] == 0.0

    bad = client.get(
        "/production/metrics",
        headers=headers,
        params={"range": "90d"},
    )
    assert bad.status_code == 422


def test_unauthenticated_production_routes(
    client: TestClient,
) -> None:
    assert client.get("/production/overview").status_code == 401
    assert client.get("/production/queue").status_code == 401
    assert client.get("/production/settings").status_code == 401
    assert client.patch(
        "/production/settings",
        json={"approved_script_target": 100},
    ).status_code == 401
