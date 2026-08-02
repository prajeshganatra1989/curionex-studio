"""Script quality review API tests — mocked OpenAI, no live provider calls."""

from __future__ import annotations

from unittest.mock import patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.credentials import reset_fernet_cache
from app.ai.providers.base import GenerationResult
from app.ai.script_draft import word_count
from app.ai.script_quality_review import (
    PURPOSE_QUALITY_REVIEW,
    REVIEW_DIMENSIONS,
    calculate_weighted_score,
    enrich_quality_review,
    parse_quality_review,
)
from app.audit.actions import (
    ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED,
    ACTION_SCRIPT_QUALITY_REVIEW_REQUESTED,
    ACTION_SCRIPT_QUALITY_SUGGESTION_APPLIED,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.ai import AiGeneration, AiPrompt, AiPromptVersion
from app.models.audit import AuditLog
from app.models.content_version import ContentVersion
from app.schemas.auth import UserCreate
from app.services import rbac_service, script_quality_service
from app.services.rbac_service import assign_role_to_user, seed_rbac_catalog
from app.services.user_service import create_user

SAMPLE_MASTER_NARRATION = (
    "Space can trap light. When a massive star collapses, gravity warps spacetime "
    "so sharply that escape velocity exceeds the speed of light. That boundary is "
    "the event horizon — not a solid surface, but a one-way door in geometry. From "
    "far away, clocks near the horizon appear to freeze. Locally, nothing dramatic "
    "happens as you cross. Matter falls inward, and our everyday intuitions about "
    "space fail. Hawking radiation remains theoretical, so treat absolute claims "
    "with care. The takeaway is simple: gravity is geometry, and black holes are "
    "regions where that geometry closes off the outside universe. Stay curious, "
    "check the sources, and explore more cosmology shorts."
)

UNIQUE_EXCERPT = "Hawking radiation remains theoretical, so treat absolute claims with care."
REWRITE_EXCERPT = (
    "Hawking radiation is still theoretical — verify any specific claims before publishing."
)


def _dim(score: int, *, assessment: str = "ok") -> dict:
    return {
        "score": score,
        "assessment": assessment,
        "strengths": ["clear"],
        "issues": [],
        "suggested_action": "none",
    }


def _sample_review(
    *,
    overall_score: int = 82,
    dim_score: int = 80,
    dim_overrides: dict[str, int] | None = None,
    priority_issues: list[dict] | None = None,
    factual_risks: list[dict] | None = None,
    recommended_next_action: str = "human_review",
) -> dict:
    scores = {key: dim_score for key in REVIEW_DIMENSIONS}
    if dim_overrides:
        scores.update(dim_overrides)
    return {
        "overall_score": overall_score,
        "confidence": "medium",
        "summary": "Strong educational short with one pacing note.",
        "ready_for_human_review": True,
        "dimensions": {
            key: _dim(value, assessment=f"{key} assessment")
            for key, value in scores.items()
        },
        "priority_issues": priority_issues
        if priority_issues is not None
        else [
            {
                "id": "iss-hook-1",
                "severity": "medium",
                "category": "clarity",
                "location_hint": "mid script",
                "original_excerpt": UNIQUE_EXCERPT,
                "problem": "Could be slightly more precise for spoken delivery.",
                "recommended_change": "Tighten the caution sentence.",
                "suggested_rewrite": REWRITE_EXCERPT,
            }
        ],
        "factual_risks": factual_risks
        if factual_risks is not None
        else [
            {
                "claim": "Exact local experience at the horizon",
                "risk_level": "low",
                "reason": "Popular-science simplification",
                "verification_needed": True,
                "related_source_note": "NASA overview",
            }
        ],
        "repeated_language": [
            {"term": "geometry", "count": 2, "suggestions": ["spacetime shape"]}
        ],
        "pacing_analysis": {
            "estimated_word_count": 120,
            "estimated_duration_seconds": 48,
            "target_duration_seconds": 60,
            "status": "within_range",
            "slow_sections": [],
            "rushed_sections": [],
        },
        "promise_analysis": {
            "promise_made": "A clear mental model of black holes",
            "promise_delivered": True,
            "explanation": "Core takeaway lands in the ending.",
        },
        "recommended_next_action": recommended_next_action,
        "warnings": [],
    }


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="Quality",
            last_name="Review",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-quality@example.com"):
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
    name: str = "Quality Review Project",
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


def _mock_result(structured: dict) -> GenerationResult:
    return GenerationResult(
        output_text="{}",
        structured_output=structured,
        tokens_input=100,
        tokens_output=50,
        tokens_total=150,
        latency_ms=42,
        provider_request_id="resp_quality_test",
        model_identifier="gpt-4o",
        raw_status="completed",
    )


def _post_review(
    client: TestClient,
    headers: dict,
    script_id: str,
    *,
    model_id: str,
    idempotency_key: str | None = None,
    **extra,
):
    body: dict = {"model_id": model_id, **extra}
    if idempotency_key is not None:
        body["idempotency_key"] = idempotency_key
    return client.post(
        f"/scripts/{script_id}/ai-quality-reviews",
        headers=headers,
        json=body,
    )


def _seed_master(
    client: TestClient,
    headers: dict,
    script_id: str,
    *,
    narration: str = SAMPLE_MASTER_NARRATION,
    discovery: str | None = "Discovery brief for black holes.",
    spine: str | None = "Hook → setup → payoff spine.",
) -> None:
    if discovery is not None:
        _put_document(client, headers, script_id, "discovery_brief", discovery)
    if spine is not None:
        _put_document(client, headers, script_id, "story_spine", spine)
    _put_document(client, headers, script_id, "master_script", narration)


# --- PROMPT ------------------------------------------------------------------


def test_quality_review_prompt_seeded_purpose_and_version(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-qr-prompt@example.com")
    prompt = script_quality_service.ensure_quality_review_prompt(
        db_session, owner=owner
    )
    assert prompt.purpose == PURPOSE_QUALITY_REVIEW
    assert prompt.active_version_id is not None

    again = script_quality_service.ensure_quality_review_prompt(
        db_session, owner=owner
    )
    assert again.id == prompt.id

    headers = _auth_header(owner)
    versions = client.get(
        f"/ai/prompts/{prompt.id}/versions", headers=headers
    ).json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1
    assert "editorial quality" in versions[0]["system_prompt"].lower() or (
        "quality reviewer" in versions[0]["system_prompt"].lower()
    )

    row = db_session.get(AiPromptVersion, prompt.active_version_id)
    assert row is not None
    assert row.version_number == 1
    assert row.system_prompt == versions[0]["system_prompt"]


# --- EMPTY / MANUAL MASTER / CONTEXT WARNINGS --------------------------------


def test_empty_master_script_blocks_review(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-empty@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Empty Master"
    )
    model_id = _setup_openai(client, headers)

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ) as mocked:
        response = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="empty-master",
        )
        assert response.status_code == 422, response.text
        assert "master script" in response.text.lower()
        assert mocked.call_count == 0


def test_manual_master_script_accepted_and_no_auto_update(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-manual@example.com")
    headers = _auth_header(owner)
    project, _pack, script = _project_pack_script(
        client, headers, name="Manual Master"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    versions_before = int(
        db_session.scalar(
            select(func.count())
            .select_from(ContentVersion)
            .where(ContentVersion.script_id == script["id"])
        )
        or 0
    )
    master_before = client.get(
        f"/scripts/{script['id']}/documents/master_script", headers=headers
    ).json()["content"]

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ) as mocked:
        response = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="manual-1",
        )
        assert response.status_code == 201, response.text
        job = response.json()
        assert job["status"] == "completed"
        assert job["purpose"] == PURPOSE_QUALITY_REVIEW
        assert job["script_id"] == script["id"]
        assert job["project_id"] == project["id"]
        assert job["document_type"] == "master_script"
        assert job["generation_id"]
        assert mocked.call_count == 1

    master_after = client.get(
        f"/scripts/{script['id']}/documents/master_script", headers=headers
    ).json()["content"]
    assert master_after == master_before

    versions_after = int(
        db_session.scalar(
            select(func.count())
            .select_from(ContentVersion)
            .where(ContentVersion.script_id == script["id"])
        )
        or 0
    )
    assert versions_after == versions_before


def test_missing_discovery_and_spine_warn_but_review_runs(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-warn@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Missing Context"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(
        client,
        headers,
        script["id"],
        discovery=None,
        spine=None,
    )
    # Ensure discovery/spine empty (seeded docs may exist empty)
    _put_document(client, headers, script["id"], "discovery_brief", "")
    _put_document(client, headers, script["id"], "story_spine", "")
    _put_document(
        client, headers, script["id"], "master_script", SAMPLE_MASTER_NARRATION
    )

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        response = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="warn-1",
        )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"

    gen = client.get(
        f"/ai/generations/{response.json()['generation_id']}", headers=headers
    ).json()
    warnings = " ".join(gen.get("warnings") or []).lower()
    assert "discovery brief" in warnings
    assert "story spine" in warnings
    structured = gen["structured_output"]
    assert "overall_score" in structured
    assert structured["ai_approval"] is False


# --- VALIDATION / SCORING / METRICS ------------------------------------------


def test_invalid_structured_output_fails_job(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-invalid@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Invalid Review"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    bad = _sample_review()
    bad["dimensions"]["hook"]["score"] = 999

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(bad),
    ):
        response = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="bad-schema",
        )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "failed"
    assert response.json()["generation_id"] is None


def test_enrichment_weighted_score_band_critical_fact_and_metrics(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-score@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Score Policy"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    # Model claims high score; dimensions yield lower weighted score; critical fact → revise
    review_payload = _sample_review(
        overall_score=95,
        dim_score=72,
        factual_risks=[
            {
                "claim": "Precise Hawking temperature at the horizon",
                "risk_level": "high",
                "reason": "Invented certainty",
                "verification_needed": False,
                "related_source_note": None,
            }
        ],
        recommended_next_action="ready_for_version",
    )

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(review_payload),
    ):
        response = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="score-1",
            target_duration_seconds=60,
            target_words_per_minute=150,
        )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"

    gen = client.get(
        f"/ai/generations/{response.json()['generation_id']}", headers=headers
    ).json()
    structured = gen["structured_output"]
    parsed = parse_quality_review(
        {
            **review_payload,
            # re-parse original model dimensions for expected weighted score
        }
    )
    expected = calculate_weighted_score(parsed.dimensions)
    assert structured["model_overall_score"] == 95
    assert structured["overall_score"] == expected
    assert structured["calculated_overall_score"] == expected
    assert structured["quality_band"]
    assert structured["recommended_next_action"] == "revise"
    assert structured["ai_approval"] is False
    assert all(
        risk["verification_needed"] is True for risk in structured["factual_risks"]
    )

    words = word_count(SAMPLE_MASTER_NARRATION)
    assert structured["deterministic_metrics"]["word_count"] == words
    assert structured["deterministic_metrics"]["estimated_duration_seconds"] == max(
        1, int(round((words / 150) * 60))
    )
    assert structured["pacing_analysis"]["estimated_word_count"] == words


# --- JOB LIFECYCLE / IDEMPOTENCY / CANCEL ------------------------------------


def test_job_idempotency_and_list_latest(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-idem@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Idempotency"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ) as mocked:
        first = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="qr-idem-1",
        )
        assert first.status_code == 201, first.text
        job = first.json()
        assert job["status"] == "completed"

        again = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="qr-idem-1",
        )
        assert again.status_code == 201, again.text
        assert again.json()["id"] == job["id"]
        assert mocked.call_count == 1

    listed = client.get(
        f"/scripts/{script['id']}/ai-quality-reviews", headers=headers
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total"] >= 1
    assert body["items"][0]["purpose"] == PURPOSE_QUALITY_REVIEW
    assert body["items"][0]["script_id"] == script["id"]

    latest = client.get(
        f"/scripts/{script['id']}/ai-quality-reviews/latest", headers=headers
    )
    assert latest.status_code == 200, latest.text
    assert latest.json()["id"] == body["items"][0]["id"]


def test_cancel_quality_review_job_before_execution(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-cancel@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Cancel QR"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    job = script_quality_service.create_quality_review_job(
        db_session,
        script_id=script["id"],
        actor=owner,
        model_id=model_id,
        idempotency_key="cancel-qr-1",
        execute_now=False,
    )
    assert job.status == "queued"

    cancelled = client.post(f"/ai/jobs/{job.id}/cancel", headers=headers)
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"


# --- FINGERPRINTS / STALE ----------------------------------------------------


def test_fingerprint_stale_when_master_changes(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-stale@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Stale QR"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        job = script_quality_service.create_quality_review_job(
            db_session,
            script_id=script["id"],
            actor=owner,
            model_id=model_id,
            idempotency_key="stale-qr-1",
            execute_now=True,
            sleep_fn=lambda _s: None,
        )
    assert job.status == "completed"
    generation = db_session.scalar(
        select(AiGeneration).where(AiGeneration.job_id == job.id)
    )
    assert generation is not None
    assert generation.input_fingerprint_json
    assert "master_script" in generation.input_fingerprint_json
    assert not script_quality_service.is_generation_stale(db_session, generation)

    _put_document(
        client,
        headers,
        script["id"],
        "master_script",
        SAMPLE_MASTER_NARRATION + " Extra sentence after review.",
    )
    db_session.refresh(generation)
    assert script_quality_service.is_generation_stale(db_session, generation)

    detail = client.get(f"/ai/generations/{generation.id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json().get("stale_input") is True


# --- SUGGESTION APPLY --------------------------------------------------------


def test_apply_unique_excerpt_and_reject_missing_duplicate_stale(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-apply@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Apply Suggestion"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="apply-ok",
        ).json()
    generation_id = job["generation_id"]

    apply_ok = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{generation_id}/"
        f"suggestions/iss-hook-1/apply",
        headers=headers,
        json={"strategy": "replace_excerpt"},
    )
    assert apply_ok.status_code == 200, apply_ok.text
    applied = apply_ok.json()
    assert applied["issue_id"] == "iss-hook-1"
    assert applied["strategy"] == "replace_excerpt"
    assert REWRITE_EXCERPT in applied["document"]["content"]
    assert UNIQUE_EXCERPT not in applied["document"]["content"]
    assert applied["stale_input"] is False

    # Restore unique excerpt once for missing / duplicate cases via new review
    _put_document(
        client,
        headers,
        script["id"],
        "master_script",
        SAMPLE_MASTER_NARRATION,
    )

    missing_review = _sample_review(
        priority_issues=[
            {
                "id": "iss-missing",
                "severity": "low",
                "category": "language",
                "location_hint": "",
                "original_excerpt": "THIS EXCERPT DOES NOT EXIST IN SCRIPT",
                "problem": "n/a",
                "recommended_change": "n/a",
                "suggested_rewrite": "replacement text",
            }
        ]
    )
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(missing_review),
    ):
        missing_job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="apply-missing",
        ).json()

    missing = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{missing_job['generation_id']}/"
        f"suggestions/iss-missing/apply",
        headers=headers,
        json={"strategy": "replace_excerpt"},
    )
    assert missing.status_code == 409, missing.text
    assert "excerpt_not_found" in missing.text or "not found" in missing.text.lower()

    duplicated = (
        SAMPLE_MASTER_NARRATION
        + " "
        + UNIQUE_EXCERPT  # second occurrence of the unique phrase
    )
    _put_document(client, headers, script["id"], "master_script", duplicated)
    # New review against duplicated content so fingerprint is fresh
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        dup_job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="apply-dup",
        ).json()

    dup = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{dup_job['generation_id']}/"
        f"suggestions/iss-hook-1/apply",
        headers=headers,
        json={"strategy": "replace_excerpt"},
    )
    assert dup.status_code == 409, dup.text
    assert "ambiguous" in dup.text.lower() or "multiple" in dup.text.lower()

    # Stale apply: review against current master, then change master
    _put_document(
        client,
        headers,
        script["id"],
        "master_script",
        SAMPLE_MASTER_NARRATION,
    )
    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        stale_job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="apply-stale",
        ).json()
    _put_document(
        client,
        headers,
        script["id"],
        "master_script",
        SAMPLE_MASTER_NARRATION + " Changed after review.",
    )
    stale = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{stale_job['generation_id']}/"
        f"suggestions/iss-hook-1/apply",
        headers=headers,
        json={"strategy": "replace_excerpt"},
    )
    assert stale.status_code == 409, stale.text
    assert "stale" in stale.text.lower()


# --- AUDIT / RBAC / SECRETS --------------------------------------------------


def test_audit_omits_full_script_and_suggestion_body(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-audit@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Audit QR"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="audit-1",
        ).json()

    apply = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{job['generation_id']}/"
        f"suggestions/iss-hook-1/apply",
        headers=headers,
        json={"strategy": "replace_excerpt"},
    )
    assert apply.status_code == 200, apply.text

    requested = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == ACTION_SCRIPT_QUALITY_REVIEW_REQUESTED
        )
    ).all()
    completed = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == ACTION_SCRIPT_QUALITY_REVIEW_COMPLETED
        )
    ).all()
    applied = db_session.scalars(
        select(AuditLog).where(
            AuditLog.action == ACTION_SCRIPT_QUALITY_SUGGESTION_APPLIED
        )
    ).all()
    assert requested
    assert completed
    assert applied

    for event in [*requested, *completed, *applied]:
        meta = event.event_metadata or {}
        blob = str(meta)
        assert SAMPLE_MASTER_NARRATION not in blob
        assert REWRITE_EXCERPT not in blob
        assert UNIQUE_EXCERPT not in blob
        assert "sk-" not in blob

    completed_meta = completed[-1].event_metadata or {}
    assert "overall_score" in completed_meta
    assert "quality_band" in completed_meta
    assert "job_id" in completed_meta

    applied_meta = applied[-1].event_metadata or {}
    assert applied_meta.get("issue_id") == "iss-hook-1"
    assert applied_meta.get("strategy") == "replace_excerpt"
    assert "suggested_rewrite" not in applied_meta
    assert "original_excerpt" not in applied_meta


def test_rbac_reviewer_cannot_generate_or_apply_suggestion(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-rbac@example.com")
    owner_headers = _auth_header(owner)
    project, _pack, script = _project_pack_script(
        client, owner_headers, name="RBAC QR"
    )
    model_id = _setup_openai(client, owner_headers)
    _seed_master(client, owner_headers, script["id"])

    reviewer = _user(db_session, "reviewer-qr@example.com")
    role = rbac_service.get_role_by_name(db_session, "Reviewer")
    assign_role_to_user(db_session, user_id=reviewer.id, role_id=role.id)
    client.post(
        f"/projects/{project['id']}/members/{reviewer.id}",
        headers=owner_headers,
    )
    reviewer_headers = _auth_header(reviewer)

    denied = _post_review(
        client,
        reviewer_headers,
        script["id"],
        model_id=model_id,
        idempotency_key="rbac-qr-1",
    )
    assert denied.status_code == 403

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        job = _post_review(
            client,
            owner_headers,
            script["id"],
            model_id=model_id,
            idempotency_key="rbac-qr-owner",
        ).json()

    # Reviewer may view
    view = client.get(
        f"/scripts/{script['id']}/ai-quality-reviews", headers=reviewer_headers
    )
    assert view.status_code == 200, view.text

    apply_denied = client.post(
        f"/scripts/{script['id']}/ai-quality-reviews/{job['generation_id']}/"
        f"suggestions/iss-hook-1/apply",
        headers=reviewer_headers,
        json={"strategy": "replace_excerpt"},
    )
    assert apply_denied.status_code == 403


def test_no_secrets_in_quality_review_responses(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-qr-secrets@example.com")
    headers = _auth_header(owner)
    _project, _pack, script = _project_pack_script(
        client, headers, name="Secrets QR"
    )
    model_id = _setup_openai(client, headers)
    _seed_master(client, headers, script["id"])

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(_sample_review()),
    ):
        job = _post_review(
            client,
            headers,
            script["id"],
            model_id=model_id,
            idempotency_key="secrets-qr",
        )
    assert "sk-test" not in job.text
    assert "sk-" not in job.text

    gen = client.get(
        f"/ai/generations/{job.json()['generation_id']}", headers=headers
    )
    assert "sk-" not in gen.text

    latest = client.get(
        f"/scripts/{script['id']}/ai-quality-reviews/latest", headers=headers
    )
    assert "sk-" not in latest.text

    prompt = db_session.scalar(
        select(AiPrompt).where(AiPrompt.purpose == PURPOSE_QUALITY_REVIEW)
    )
    assert prompt is not None
    detail = client.get(f"/ai/prompts/{prompt.id}", headers=headers)
    assert "sk-" not in detail.text


def test_enrich_helper_parity_with_executor_path() -> None:
    """Sanity: sample payload enrich matches expected policy without HTTP."""
    review = parse_quality_review(_sample_review(overall_score=90, dim_score=85))
    enriched = enrich_quality_review(
        review,
        master_script=SAMPLE_MASTER_NARRATION,
        context_warnings=["Story Spine is empty."],
    )
    assert enriched["ai_approval"] is False
    assert enriched["model_overall_score"] == 90
    assert enriched["overall_score"] == calculate_weighted_score(review.dimensions)
    assert "Story Spine is empty." in enriched["warnings"]
    assert 100 <= word_count(SAMPLE_MASTER_NARRATION) <= 150
