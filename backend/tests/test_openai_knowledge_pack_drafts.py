"""OpenAI Knowledge Pack drafting tests — mocked provider, no live API calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.credentials import reset_fernet_cache
from app.ai.knowledge_pack_draft import (
    PURPOSE_KNOWLEDGE_PACK_DRAFT,
    draft_section_to_plain_text,
    parse_knowledge_pack_draft,
)
from app.ai.providers.base import GenerationResult
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.ai import AiGeneration
from app.models.audit import AuditLog
from app.schemas.auth import UserCreate
from app.services import rbac_service
from app.services.rbac_service import seed_rbac_catalog
from app.services.user_service import create_user

SAMPLE_DRAFT = {
    "research": "Black holes bend spacetime.",
    "facts": ["Event horizons exist", "Hawking radiation is theoretical"],
    "sources": [
        {
            "label": "NASA",
            "reference": "https://example.com/bh",
            "verification_status": "verified",
        }
    ],
    "audience": "Curious adults",
    "content_angle": "Accessible astrophysics",
    "key_insights": ["Gravity is geometry"],
    "additional_context": "Keep language plain.",
    "warnings": ["Sources are unverified"],
}


def _user(db: Session, email: str):
    return create_user(
        db,
        UserCreate(
            email=email,
            password="securepass123",
            first_name="KP",
            last_name="AI",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-kp-ai@example.com"):
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


def _project_and_pack(client: TestClient, headers: dict) -> tuple[dict, dict]:
    project = client.post(
        "/projects", headers=headers, json={"name": "AI Draft Project"}
    )
    assert project.status_code == 201, project.text
    pack = client.post(
        f"/projects/{project.json()['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Research Pack"},
    )
    assert pack.status_code == 201, pack.text
    return project.json(), pack.json()


def _mock_result() -> GenerationResult:
    return GenerationResult(
        output_text="{}",
        structured_output=SAMPLE_DRAFT,
        tokens_input=100,
        tokens_output=50,
        tokens_total=150,
        latency_ms=42,
        provider_request_id="resp_test_123",
        model_identifier="gpt-4o",
        raw_status="completed",
    )


def test_draft_schema_forces_unverified_sources() -> None:
    draft = parse_knowledge_pack_draft(SAMPLE_DRAFT)
    assert draft.sources[0].verification_status == "unverified"
    text = draft_section_to_plain_text("sources", draft)
    assert "UNVERIFIED" in text
    assert "HUMAN CHECK REQUIRED" in text


def test_openai_adapter_normalizes_mocked_response(monkeypatch) -> None:
    from app.ai.providers.base import GenerationRequest
    from app.ai.providers.openai_provider import OpenAIProvider

    provider = OpenAIProvider()
    fake_response = MagicMock()
    fake_response.output_text = '{"research":"x","facts":[],"sources":[],"audience":"","content_angle":"","key_insights":[],"additional_context":"","warnings":[]}'
    fake_response.usage.input_tokens = 10
    fake_response.usage.output_tokens = 5
    fake_response.usage.total_tokens = 15
    fake_response.id = "resp_abc"
    fake_response.model = "gpt-4o"
    fake_response.status = "completed"
    fake_response.output = []

    client = MagicMock()
    client.responses.create.return_value = fake_response

    with patch("app.ai.providers.openai_provider.OpenAI", return_value=client):
        result = provider.generate(
            GenerationRequest(
                model_code="gpt-4o",
                system_prompt="sys",
                user_prompt="user",
                api_key="sk-test-key",
                response_json_schema={"type": "object"},
                response_schema_name="test",
            )
        )
    assert result.provider_request_id == "resp_abc"
    assert result.tokens_input == 10
    assert result.structured_output is not None
    assert "sk-test" not in str(result)


def test_knowledge_pack_draft_job_and_apply(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session)
    headers = _auth_header(owner)
    project, pack = _project_and_pack(client, headers)

    providers = client.get("/ai/providers", headers=headers).json()
    openai = next(p for p in providers if p["code"] == "openai")
    cred = client.post(
        f"/ai/providers/{openai['id']}/credentials",
        headers=headers,
        json={"api_key": "sk-test-not-real"},
    )
    assert cred.status_code == 200

    models = client.get(
        f"/ai/models?provider_id={openai['id']}", headers=headers
    ).json()
    model_id = models[0]["id"]

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(),
    ) as mocked:
        response = client.post(
            f"/projects/{project['id']}/knowledge-packs/{pack['id']}/ai-drafts",
            headers=headers,
            json={
                "model_id": model_id,
                "target_audience": "teens",
                "language": "en",
                "desired_depth": "deep",
                "idempotency_key": "idem-1",
            },
        )
        assert response.status_code == 201, response.text
        job = response.json()
        assert job["status"] == "completed"
        assert job["purpose"] == PURPOSE_KNOWLEDGE_PACK_DRAFT
        assert job["generation_id"]
        assert mocked.call_count == 1

        # Idempotent replay must not call provider again.
        again = client.post(
            f"/projects/{project['id']}/knowledge-packs/{pack['id']}/ai-drafts",
            headers=headers,
            json={
                "model_id": model_id,
                "idempotency_key": "idem-1",
            },
        )
        assert again.status_code == 201
        assert again.json()["id"] == job["id"]
        assert mocked.call_count == 1

    generation_id = job["generation_id"]
    gen = client.get(f"/ai/generations/{generation_id}", headers=headers)
    assert gen.status_code == 200
    body = gen.json()
    assert (
        body["structured_output"]["sources"][0]["verification_status"] == "unverified"
    )
    assert body["tokens_total"] == 150
    assert body["cost_usd"] is not None
    assert "sk-" not in gen.text

    # Default conflict strategy allows empty sections.
    apply = client.post(
        f"/knowledge-packs/{pack['id']}/ai-generations/{generation_id}/apply",
        headers=headers,
        json={
            "sections": ["research", "facts", "sources"],
            "conflict_strategy": "reject_if_non_empty",
        },
    )
    assert apply.status_code == 200, apply.text
    applied = apply.json()["applied_sections"]
    assert set(applied) == {"research", "facts", "sources"}

    detail = client.get(f"/knowledge-packs/{pack['id']}", headers=headers).json()
    by_key = {s["section_key"]: s["content"] for s in detail["sections"]}
    assert "Black holes" in by_key["research"]
    assert by_key["facts"].startswith("- ")
    assert "UNVERIFIED" in by_key["sources"]
    assert by_key["audience"] == ""  # unselected unchanged

    # reject_if_non_empty blocks second apply
    blocked = client.post(
        f"/knowledge-packs/{pack['id']}/ai-generations/{generation_id}/apply",
        headers=headers,
        json={
            "sections": ["research"],
            "conflict_strategy": "reject_if_non_empty",
        },
    )
    assert blocked.status_code == 409

    # replace_selected works
    replaced = client.post(
        f"/knowledge-packs/{pack['id']}/ai-generations/{generation_id}/apply",
        headers=headers,
        json={
            "sections": ["research"],
            "conflict_strategy": "replace_selected",
        },
    )
    assert replaced.status_code == 200

    # Generation retained
    assert db_session.get(AiGeneration, generation_id) is not None
    audits = db_session.scalars(select(AuditLog)).all()
    for event in audits:
        meta = str(event.event_metadata or {})
        assert "sk-" not in meta
        assert "Black holes bend" not in meta


def test_cross_project_apply_rejected(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-cross@example.com")
    headers = _auth_header(owner)
    project_a, pack_a = _project_and_pack(client, headers)
    project_b = client.post(
        "/projects", headers=headers, json={"name": "Other Project"}
    ).json()
    pack_b = client.post(
        f"/projects/{project_b['id']}/knowledge-packs",
        headers=headers,
        json={"name": "Other Pack"},
    ).json()

    providers = client.get("/ai/providers", headers=headers).json()
    openai = next(p for p in providers if p["code"] == "openai")
    client.post(
        f"/ai/providers/{openai['id']}/credentials",
        headers=headers,
        json={"api_key": "sk-test-not-real"},
    )
    model_id = client.get(
        f"/ai/models?provider_id={openai['id']}", headers=headers
    ).json()[0]["id"]

    with patch(
        "app.ai.providers.openai_provider.OpenAIProvider.generate",
        return_value=_mock_result(),
    ):
        job = client.post(
            f"/projects/{project_a['id']}/knowledge-packs/{pack_a['id']}/ai-drafts",
            headers=headers,
            json={"model_id": model_id, "idempotency_key": "cross-1"},
        ).json()

    bad = client.post(
        f"/knowledge-packs/{pack_b['id']}/ai-generations/{job['generation_id']}/apply",
        headers=headers,
        json={"sections": ["research"], "conflict_strategy": "replace_selected"},
    )
    assert bad.status_code in {403, 404}


def test_cancel_queued_job_before_execution(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-cancel@example.com")
    headers = _auth_header(owner)
    # Create a plain queued job via prompt path (no provider call).
    prompt = client.post(
        "/ai/prompts",
        headers=headers,
        json={
            "name": "Temp",
            "purpose": "temp",
            "system_prompt": "S",
            "user_template": "T {{topic}}",
            "variables": ["topic"],
        },
    ).json()
    model = client.get("/ai/models", headers=headers).json()[0]
    job = client.post(
        "/ai/jobs",
        headers=headers,
        json={
            "prompt_id": prompt["id"],
            "model_id": model["id"],
            "input_variables": {"topic": "x"},
        },
    ).json()
    assert job["status"] == "queued"
    cancelled = client.post(f"/ai/jobs/{job['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
