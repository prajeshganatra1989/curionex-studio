"""Script Document AI draft pipeline tests — mocked provider, no live API calls."""

from __future__ import annotations

from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.constants import JOB_STATUS_FAILED
from app.ai.credentials import reset_fernet_cache
from app.ai.errors import ProviderRequestError, StructuredOutputError
from app.ai.providers.base import GenerationResult
from app.ai.script_draft import (
    PURPOSE_DISCOVERY_BRIEF,
    PURPOSE_MASTER_SCRIPT,
    PURPOSE_STORY_SPINE,
    SCRIPT_DRAFT_PURPOSES,
    discovery_brief_to_plain_text,
    master_script_to_plain_text,
    parse_discovery_brief,
    parse_master_script,
    parse_story_spine,
    story_spine_to_plain_text,
    word_count,
)
from app.audit.actions import (
    ACTION_SCRIPT_AI_DRAFT_APPLIED,
    ACTION_SCRIPT_AI_DRAFT_REQUESTED,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.ai import AiGeneration, AiJob, AiPrompt, AiPromptVersion
from app.models.audit import AuditLog
from app.models.content_version import ContentVersion
from app.schemas.auth import UserCreate
from app.services import rbac_service, script_ai_service
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user

SAMPLE_DISCOVERY = {
    "topic": "Black holes",
    "working_title": "Edge of Darkness",
    "core_question": "What happens at the event horizon?",
    "viewer_promise": "A clear mental model of black holes",
    "target_audience": "Curious adults",
    "core_takeaway": "Gravity warps spacetime",
    "content_angle": "Accessible astrophysics",
    "key_facts": ["Event horizons exist", "Hawking radiation is theoretical"],
    "claims_requiring_verification": ["Exact horizon behavior"],
    "source_notes": ["NASA overview"],
    "emotional_direction": "Wonder without fear",
    "visual_opportunities": ["Spacetime grid warp"],
    "risks_and_cautions": ["Avoid sensational claims"],
    "recommended_duration_seconds": 60,
}

SAMPLE_SPINE = {
    "hook": "Space can trap light.",
    "setup": "A star collapses.",
    "curiosity_gap": "Where does the matter go?",
    "progression": [
        {
            "beat": 1,
            "purpose": "establish",
            "content": "Mass curves spacetime.",
            "estimated_seconds": 8,
        },
        {
            "beat": 2,
            "purpose": "escalate",
            "content": "Escape velocity exceeds light.",
            "estimated_seconds": 10,
        },
    ],
    "core_explanation": "The horizon is a boundary in spacetime.",
    "reveal_or_reframe": "Nothing dramatic happens locally.",
    "ending": "Gravity is geometry.",
    "call_to_action": "Explore more cosmology shorts.",
    "visual_rhythm_notes": ["Slow push-in"],
    "retention_risks": ["Jargon overload"],
    "claims_requiring_verification": ["Exact collapse dynamics"],
    "estimated_total_seconds": 60,
}


def _narration(n: int) -> str:
    return " ".join(["word"] * n)


def _master(*, narration: str) -> dict:
    return {
        "title": "Edge of Darkness",
        "narration": narration,
        "hook": "Space can trap light.",
        "ending": "Gravity is geometry.",
        "estimated_word_count": word_count(narration),
        "estimated_duration_seconds": 60,
        "on_screen_keywords": ["horizon", "spacetime"],
        "claims_requiring_verification": ["Exact horizon behavior"],
        "editor_notes": ["Keep spoken cadence"],
        "quality_checks": {
            "single_core_idea": True,
            "clear_hook": True,
            "clear_payoff": True,
            "duration_target_met": True,
        },
    }


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Script",
            last_name="AI",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-script-ai@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _enable_credentials_key(monkeypatch) -> str:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("AI_CREDENTIALS_KEY", key)
    get_settings.cache_clear()
    reset_fernet_cache()
    return key


def _project_pack_script(
    client: TestClient,
    headers: dict,
    *,
    name: str = "Script AI Project",
) -> tuple[dict, dict, dict]:
    project = client.post("/projects", headers=headers, json={"name": name})
    assert project.status_code == 201, project.text
    pack = client.post(
        f"/projects/{project.json()['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Research Pack"},
    )
    assert pack.status_code == 201, pack.text
    script = client.post(
        f"/projects/{project.json()['id']}/scripts",
        headers=headers,
        json={
            "title": "Main Script",
            "knowledge_pack_id": pack.json()["id"],
        },
    )
    assert script.status_code == 201, script.text
    return project.json(), pack.json(), script.json()


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


def _put_document(
    client: TestClient,
    headers: dict,
    script_id: str,
    document_type: str,
    content: str,
) -> dict:
    response = client.patch(
        f"/scripts/{script_id}/documents/{document_type}",
        headers=headers,
        json={"content": content},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _mock_result(
    structured: dict,
    *,
    tokens_input: int = 100,
    tokens_output: int = 50,
) -> GenerationResult:
    return GenerationResult(
        output_text="{}",
        structured_output=structured,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_total=tokens_input + tokens_output,
        latency_ms=42,
        provider_request_id="resp_script_test",
        model_identifier="gpt-4o",
        raw_status="completed",
    )


def _post_draft(
    client: TestClient,
    headers: dict,
    script_id: str,
    document_type: str,
    *,
    model_id: str,
    idempotency_key: str | None = None,
    **extra,
):
    body: dict = {"model_id": model_id, **extra}
    if idempotency_key is not None:
        body["idempotency_key"] = idempotency_key
    return client.post(
        f"/scripts/{script_id}/documents/{document_type}/ai-drafts",
        headers=headers,
        json=body,
    )


# --- PROMPTS -----------------------------------------------------------------


def test_script_draft_prompts_seeded_unique_immutable(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-prompts@example.com")
    prompts = script_ai_service.ensure_script_draft_prompts(db_session, owner=owner)

    assert set(prompts.keys()) == SCRIPT_DRAFT_PURPOSES
    purposes = [p.purpose for p in prompts.values()]
    assert len(purposes) == len(set(purposes)) == 3

    again = script_ai_service.ensure_script_draft_prompts(db_session, owner=owner)
    assert {p.id for p in again.values()} == {p.id for p in prompts.values()}

    headers = _auth_header(owner)
    discovery = prompts[PURPOSE_DISCOVERY_BRIEF]
    listed = client.get(f"/ai/prompts/{discovery.id}/versions", headers=headers)
    assert listed.status_code == 200, listed.text
    versions = listed.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    original_system = versions[0]["system_prompt"]

    v2 = client.post(
        f"/ai/prompts/{discovery.id}/versions",
        headers=headers,
        json={
            "system_prompt": "Updated system prompt for immutability check.",
            "user_template": versions[0]["user_template"],
            "variables": versions[0]["variables"],
        },
    )
    assert v2.status_code == 201, v2.text
    assert v2.json()["version_number"] == 2

    refreshed = client.get(
        f"/ai/prompts/{discovery.id}/versions", headers=headers
    ).json()
    by_num = {item["version_number"]: item for item in refreshed}
    assert by_num[1]["system_prompt"] == original_system
    assert by_num[1]["system_prompt"] != by_num[2]["system_prompt"]

    row = db_session.get(AiPromptVersion, discovery.active_version_id)
    assert row is not None
    assert row.version_number == 1
    assert row.system_prompt == original_system


# --- DISCOVERY / CONTEXT / JOBS ----------------------------------------------


def test_discovery_brief_draft_linked_no_auto_apply(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-discovery@example.com")
    headers = _auth_header(owner)
    project, _pack, script = _project_pack_script(client, headers)
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ) as mocked:
        response = _post_draft(
            client,
            headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="disc-1",
            language="English",
            tone="curious",
        )
        assert response.status_code == 201, response.text
        job = response.json()
        assert job["status"] == "completed"
        assert job["purpose"] == PURPOSE_DISCOVERY_BRIEF
        assert job["project_id"] == project["id"]
        assert job["script_id"] == script["id"]
        assert job["document_type"] == "discovery_brief"
        assert job["generation_id"]
        assert mocked.call_count == 1

        again = _post_draft(
            client,
            headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="disc-1",
        )
        assert again.status_code == 201
        assert again.json()["id"] == job["id"]
        assert mocked.call_count == 1

    doc = client.get(
        f"/scripts/{script['id']}/documents/discovery_brief", headers=headers
    ).json()
    assert (doc.get("content") or "").strip() == ""

    gen = client.get(f"/ai/generations/{job['generation_id']}", headers=headers)
    assert gen.status_code == 200, gen.text
    body = gen.json()
    assert body["script_id"] == script["id"]
    assert body["document_type"] == "discovery_brief"
    assert body["project_id"] == project["id"]
    assert body["structured_output"]["topic"] == "Black holes"
    assert body["input_fingerprint"] is not None
    assert "sk-" not in gen.text

    expected_plain = discovery_brief_to_plain_text(
        parse_discovery_brief(SAMPLE_DISCOVERY)
    )
    # Structured conversion must be deterministic; apply later uses same path.
    assert "TOPIC\nBlack holes" in expected_plain

    jobs = db_session.scalars(
        select(AiJob).where(
            AiJob.script_id == script["id"],
            AiJob.document_type == "discovery_brief",
        )
    ).all()
    assert len(jobs) == 1


# --- STORY SPINE / MASTER PREREQUISITES --------------------------------------


def test_story_spine_and_master_prerequisites_block(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-prereq@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Prereq Project"
    )
    model_id = _setup_openai(client, headers)

    spine_prereq = client.get(
        f"/scripts/{script['id']}/documents/story_spine/ai-prerequisites",
        headers=headers,
    )
    assert spine_prereq.status_code == 200, spine_prereq.text
    spine_body = spine_prereq.json()
    assert spine_body["document_type"] == "story_spine"
    assert spine_body["ready"] is False
    assert "discovery_brief" in spine_body["missing"]

    master_prereq = client.get(
        f"/scripts/{script['id']}/documents/master_script/ai-prerequisites",
        headers=headers,
    ).json()
    assert master_prereq["ready"] is False
    assert set(master_prereq["missing"]) == {"discovery_brief", "story_spine"}

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_SPINE),
    ) as mocked:
        blocked = _post_draft(
            client,
            headers,
            script["id"],
            "story_spine",
            model_id=model_id,
            idempotency_key="spine-block",
        )
        assert blocked.status_code in {409, 422}, blocked.text
        detail = blocked.text.lower()
        assert "missing" in detail or "prerequisite" in detail
        assert mocked.call_count == 0

        master_blocked = _post_draft(
            client,
            headers,
            script["id"],
            "master_script",
            model_id=model_id,
            idempotency_key="master-block",
        )
        assert master_blocked.status_code in {409, 422}, master_blocked.text
        assert mocked.call_count == 0


def test_story_spine_draft_after_discovery_ready(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-spine@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Spine Project"
    )
    model_id = _setup_openai(client, headers)

    _put_document(
        client,
        headers,
        script["id"],
        "discovery_brief",
        discovery_brief_to_plain_text(parse_discovery_brief(SAMPLE_DISCOVERY)),
    )
    ready = client.get(
        f"/scripts/{script['id']}/documents/story_spine/ai-prerequisites",
        headers=headers,
    ).json()
    assert ready["ready"] is True
    assert ready["missing"] == []

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_SPINE),
    ):
        response = _post_draft(
            client,
            headers,
            script["id"],
            "story_spine",
            model_id=model_id,
            idempotency_key="spine-1",
        )
    assert response.status_code == 201, response.text
    job = response.json()
    assert job["purpose"] == PURPOSE_STORY_SPINE
    assert job["document_type"] == "story_spine"
    assert job["status"] == "completed"

    gen = client.get(
        f"/ai/generations/{job['generation_id']}", headers=headers
    ).json()
    assert gen["structured_output"]["hook"] == "Space can trap light."
    assert [b["beat"] for b in gen["structured_output"]["progression"]] == [1, 2]


def test_invalid_story_spine_beats_fail_job(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-bad-beats@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Bad Beats Project"
    )
    model_id = _setup_openai(client, headers)
    _put_document(
        client,
        headers,
        script["id"],
        "discovery_brief",
        "Discovery brief content for beat validation.",
    )

    bad_spine = dict(SAMPLE_SPINE)
    bad_spine["progression"] = [
        {
            "beat": 1,
            "purpose": "a",
            "content": "x",
            "estimated_seconds": 5,
        },
        {
            "beat": 3,
            "purpose": "b",
            "content": "y",
            "estimated_seconds": 5,
        },
    ]
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(bad_spine),
    ):
        response = _post_draft(
            client,
            headers,
            script["id"],
            "story_spine",
            model_id=model_id,
            idempotency_key="bad-beats",
        )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "failed"
    assert response.json()["generation_id"] is None


# --- MASTER DURATION REPAIR --------------------------------------------------


def _seed_master_ready(
    client: TestClient, headers: dict, script_id: str
) -> None:
    _put_document(
        client,
        headers,
        script_id,
        "discovery_brief",
        discovery_brief_to_plain_text(parse_discovery_brief(SAMPLE_DISCOVERY)),
    )
    _put_document(
        client,
        headers,
        script_id,
        "story_spine",
        story_spine_to_plain_text(parse_story_spine(SAMPLE_SPINE)),
    )


def test_master_script_one_duration_repair_and_usage(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-repair@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Repair Project"
    )
    model_id = _setup_openai(client, headers)
    _seed_master_ready(client, headers, script["id"])

    too_long = _master(narration=_narration(300))
    repaired = _master(narration=_narration(150))
    results = [
        _mock_result(too_long, tokens_input=100, tokens_output=50),
        _mock_result(repaired, tokens_input=40, tokens_output=20),
    ]

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        side_effect=results,
    ) as mocked:
        response = _post_draft(
            client,
            headers,
            script["id"],
            "master_script",
            model_id=model_id,
            idempotency_key="master-repair",
            target_duration_seconds=60,
            target_words_per_minute=150,
        )
    assert response.status_code == 201, response.text
    job = response.json()
    assert job["status"] == "completed"
    assert job["purpose"] == PURPOSE_MASTER_SCRIPT
    assert mocked.call_count == 2

    gen = client.get(
        f"/ai/generations/{job['generation_id']}", headers=headers
    ).json()
    assert word_count(gen["structured_output"]["narration"]) == 150
    assert gen["tokens_input"] == 140
    assert gen["tokens_output"] == 70
    warnings = gen.get("warnings") or []
    assert any("repaired" in w.lower() for w in warnings)

    # Narration-only apply path
    apply = client.post(
        f"/scripts/{script['id']}/documents/master_script/"
        f"ai-generations/{job['generation_id']}/apply",
        headers=headers,
        json={"conflict_strategy": "reject_if_non_empty"},
    )
    assert apply.status_code == 200, apply.text
    document = apply.json()["document"]
    expected = master_script_to_plain_text(parse_master_script(repaired))
    assert document["content"] == expected
    assert document["content"] == _narration(150)
    assert "Edge of Darkness" not in document["content"]
    assert "Keep spoken cadence" not in document["content"]


def test_master_script_no_unlimited_repair(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-no-loop@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="No Loop Project"
    )
    model_id = _setup_openai(client, headers)
    _seed_master_ready(client, headers, script["id"])

    always_long = _mock_result(_master(narration=_narration(300)))
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=always_long,
    ) as mocked:
        response = _post_draft(
            client,
            headers,
            script["id"],
            "master_script",
            model_id=model_id,
            idempotency_key="master-no-loop",
            target_duration_seconds=60,
            target_words_per_minute=150,
        )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"
    assert mocked.call_count == 2  # initial + one repair only

    gen = client.get(
        f"/ai/generations/{response.json()['generation_id']}", headers=headers
    ).json()
    assert word_count(gen["structured_output"]["narration"]) == 300
    warnings = gen.get("warnings") or []
    assert any("one repair" in w.lower() or "still outside" in w.lower() for w in warnings)


# --- JOBS: cancel / retry ----------------------------------------------------


def test_cancel_script_draft_job_before_execution(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-cancel-script@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Cancel Project"
    )
    model_id = _setup_openai(client, headers)

    job = script_ai_service.create_script_document_draft_job(
        db_session,
        script_id=script["id"],
        document_type="discovery_brief",
        actor=owner,
        model_id=model_id,
        idempotency_key="cancel-1",
        execute_now=False,
    )
    assert job.status == "queued"

    cancelled = client.post(f"/ai/jobs/{job.id}/cancel", headers=headers)
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"


def test_retryable_vs_non_retryable_provider_errors(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-retry@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Retry Project"
    )
    model_id = _setup_openai(client, headers)

    calls = {"n": 0}

    def flaky_then_ok(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ProviderRequestError("provider timeout", retryable=True)
        return _mock_result(SAMPLE_DISCOVERY)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        side_effect=flaky_then_ok,
    ):
        ok_job = script_ai_service.create_script_document_draft_job(
            db_session,
            script_id=script["id"],
            document_type="discovery_brief",
            actor=owner,
            model_id=model_id,
            idempotency_key="retry-ok",
            execute_now=True,
            sleep_fn=lambda _s: None,
        )
    assert ok_job.status == "completed"
    assert ok_job.retries >= 1
    assert calls["n"] == 2

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        side_effect=StructuredOutputError("invalid structured output"),
    ):
        failed = script_ai_service.create_script_document_draft_job(
            db_session,
            script_id=script["id"],
            document_type="discovery_brief",
            actor=owner,
            model_id=model_id,
            idempotency_key="retry-fail",
            execute_now=True,
            sleep_fn=lambda _s: None,
        )
    assert failed.status == "failed"
    assert failed.retries == 0
    assert (
        db_session.scalar(
            select(AiGeneration).where(AiGeneration.job_id == failed.id)
        )
        is None
    )


# --- STALE FINGERPRINT -------------------------------------------------------


def test_fingerprint_stored_and_stale_when_source_changes(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-stale@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Stale Project"
    )
    model_id = _setup_openai(client, headers)
    _put_document(
        client,
        headers,
        script["id"],
        "discovery_brief",
        "Original discovery brief.",
    )

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_SPINE),
    ):
        job = script_ai_service.create_script_document_draft_job(
            db_session,
            script_id=script["id"],
            document_type="story_spine",
            actor=owner,
            model_id=model_id,
            idempotency_key="stale-1",
            execute_now=True,
            sleep_fn=lambda _s: None,
        )
    assert job.status == "completed"
    generation = db_session.scalar(
        select(AiGeneration).where(AiGeneration.job_id == job.id)
    )
    assert generation is not None
    assert generation.input_fingerprint_json
    assert generation.input_fingerprint_json.get("document_type") == "story_spine"
    assert not script_ai_service.is_generation_stale(db_session, generation)

    _put_document(
        client,
        headers,
        script["id"],
        "discovery_brief",
        "Discovery brief changed after generation.",
    )
    db_session.refresh(generation)
    assert script_ai_service.is_generation_stale(db_session, generation)


# --- APPLY -------------------------------------------------------------------


def test_apply_strategies_and_auditing(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-apply@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Apply Project"
    )
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ):
        job = _post_draft(
            client,
            headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="apply-1",
        ).json()
    generation_id = job["generation_id"]

    versions_before = int(
        db_session.scalar(
            select(func.count())
            .select_from(ContentVersion)
            .where(ContentVersion.script_id == script["id"])
        )
        or 0
    )

    apply = client.post(
        f"/scripts/{script['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "reject_if_non_empty"},
    )
    assert apply.status_code == 200, apply.text
    applied = apply.json()
    assert applied["generation_id"] == generation_id
    assert applied["conflict_strategy"] == "reject_if_non_empty"
    assert "TOPIC\nBlack holes" in applied["document"]["content"]
    assert "stale_input" in applied

    versions_after = int(
        db_session.scalar(
            select(func.count())
            .select_from(ContentVersion)
            .where(ContentVersion.script_id == script["id"])
        )
        or 0
    )
    assert versions_after == versions_before

    blocked = client.post(
        f"/scripts/{script['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "reject_if_non_empty"},
    )
    assert blocked.status_code == 409

    replaced = client.post(
        f"/scripts/{script['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "replace"},
    )
    assert replaced.status_code == 200, replaced.text
    assert "TOPIC\nBlack holes" in replaced.json()["document"]["content"]

    appended = client.post(
        f"/scripts/{script['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "append"},
    )
    assert appended.status_code == 200, appended.text
    content = appended.json()["document"]["content"]
    assert content.count("TOPIC\nBlack holes") == 2

    audits = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_SCRIPT_AI_DRAFT_APPLIED)
    ).all()
    assert audits
    for event in audits:
        meta = str(event.event_metadata or {})
        assert "sk-" not in meta

    requested = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_SCRIPT_AI_DRAFT_REQUESTED)
    ).all()
    assert requested


def test_apply_wrong_script_type_and_failed_job_rejected(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-apply-bad@example.com")
    headers = _auth_header(owner)
    _project_a, _pack_a, script_a = _project_pack_script(
        client, headers, name="Apply A"
    )
    _project_b, _pack_b, script_b = _project_pack_script(
        client, headers, name="Apply B"
    )
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ):
        job = _post_draft(
            client,
            headers,
            script_a["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="apply-cross",
        ).json()
    generation_id = job["generation_id"]

    wrong_script = client.post(
        f"/scripts/{script_b['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "replace"},
    )
    assert wrong_script.status_code in {403, 404}, wrong_script.text

    wrong_type = client.post(
        f"/scripts/{script_a['id']}/documents/story_spine/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "replace"},
    )
    assert wrong_type.status_code in {403, 404, 422}, wrong_type.text

    generation = db_session.get(AiGeneration, generation_id)
    assert generation is not None
    failed_job = db_session.get(AiJob, generation.job_id)
    assert failed_job is not None
    failed_job.status = JOB_STATUS_FAILED
    db_session.commit()

    cannot = client.post(
        f"/scripts/{script_a['id']}/documents/discovery_brief/"
        f"ai-generations/{generation_id}/apply",
        headers=headers,
        json={"conflict_strategy": "replace"},
    )
    assert cannot.status_code in {409, 422}, cannot.text


# --- LIST / SECURITY ---------------------------------------------------------


def test_list_drafts_endpoint(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-list@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="List Project"
    )
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ):
        _post_draft(
            client,
            headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="list-1",
        )

    listed = client.get(f"/scripts/{script['id']}/ai-drafts", headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    assert body["items"][0]["script_id"] == script["id"]
    assert body["items"][0]["document_type"] == "discovery_brief"

    filtered = client.get(
        f"/scripts/{script['id']}/ai-drafts?document_type=discovery_brief",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert all(
        item["document_type"] == "discovery_brief" for item in filtered.json()["items"]
    )


def test_rbac_reviewer_cannot_generate_or_apply(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-rbac-ai@example.com")
    owner_headers = _auth_header(owner)
    project, _pack, script = _project_pack_script(
        client, owner_headers, name="RBAC AI Project"
    )
    model_id = _setup_openai(client, owner_headers)

    reviewer = _user(db_session, "reviewer-script-ai@example.com")
    role = rbac_service.get_role_by_name(db_session, "Reviewer")
    assign_role_to_user(db_session, user_id=reviewer.id, role_id=role.id)
    client.post(
        f"/projects/{project['id']}/members/{reviewer.id}",
        headers=owner_headers,
    )
    reviewer_headers = _auth_header(reviewer)

    denied = _post_draft(
        client,
        reviewer_headers,
        script["id"],
        "discovery_brief",
        model_id=model_id,
        idempotency_key="rbac-1",
    )
    assert denied.status_code == 403

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ):
        job = _post_draft(
            client,
            owner_headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="rbac-owner",
        ).json()

    apply_denied = client.post(
        f"/scripts/{script['id']}/documents/discovery_brief/"
        f"ai-generations/{job['generation_id']}/apply",
        headers=reviewer_headers,
        json={"conflict_strategy": "replace"},
    )
    assert apply_denied.status_code == 403


def test_no_secrets_in_responses(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-secrets@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Secrets Project"
    )
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(SAMPLE_DISCOVERY),
    ):
        job = _post_draft(
            client,
            headers,
            script["id"],
            "discovery_brief",
            model_id=model_id,
            idempotency_key="secrets-1",
        )
    assert "sk-test" not in job.text
    assert "sk-" not in job.text

    gen = client.get(
        f"/ai/generations/{job.json()['generation_id']}", headers=headers
    )
    assert "sk-" not in gen.text

    providers = client.get("/ai/providers", headers=headers)
    assert "sk-" not in providers.text

    prompts = db_session.scalars(select(AiPrompt)).all()
    assert prompts  # seeded by draft request
    for prompt in prompts:
        if prompt.purpose in SCRIPT_DRAFT_PURPOSES:
            detail = client.get(f"/ai/prompts/{prompt.id}", headers=headers)
            assert "sk-" not in detail.text
