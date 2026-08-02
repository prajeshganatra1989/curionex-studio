"""AI foundation tests — providers, prompts, jobs, RBAC, audit, encryption."""

from __future__ import annotations

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.credentials import decrypt_secret, reset_fernet_cache
from app.ai.prompt_renderer import extract_variables, render_template
from app.ai.providers import get_provider, list_provider_codes
from app.ai.retry import decide_retry
from app.audit.actions import (
    ACTION_AI_JOB_CANCELLED,
    ACTION_AI_JOB_QUEUED,
    ACTION_AI_PROMPT_CREATED,
    ACTION_AI_PROVIDER_CREDENTIALS_SET,
    ACTION_AI_SETTINGS_CHANGED,
)
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.ai import AiProvider
from app.models.audit import AuditLog
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
            first_name="AI",
            last_name="Tester",
        ),
    )


def _auth_header(user) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


def _owner(db: Session, email: str = "owner-ai@example.com"):
    seed_rbac_catalog(db)
    user = _user(db, email)
    rbac_service.assign_owner_role(db, user)
    return user


def _role_user(db: Session, email: str, role_name: str):
    seed_rbac_catalog(db)
    user = _user(db, email)
    role = rbac_service.get_role_by_name(db, role_name)
    assert role is not None
    rbac_service.assign_role_to_user(db, user_id=user.id, role_id=role.id)
    return user


def _enable_credentials_key(monkeypatch) -> str:
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("AI_CREDENTIALS_KEY", key)
    get_settings.cache_clear()
    reset_fernet_cache()
    return key


def test_provider_registry_includes_openai_adapter() -> None:
    codes = list_provider_codes()
    assert "openai" in codes
    assert "anthropic" in codes
    provider = get_provider("openai")
    assert provider.code == "openai"
    # Live adapter rejects missing credentials without calling the network.
    from app.ai.errors import ProviderConfigurationError
    from app.ai.providers.base import GenerationRequest

    try:
        provider.generate(
            GenerationRequest(
                model_code="gpt-4o",
                system_prompt="sys",
                user_prompt="user",
                api_key=None,
            )
        )
        raise AssertionError("expected ProviderConfigurationError")
    except ProviderConfigurationError:
        pass

    # Non-OpenAI providers remain stubs.
    from app.ai.providers.base import ProviderNotImplementedError

    try:
        get_provider("anthropic").generate(
            GenerationRequest(
                model_code="claude",
                system_prompt="sys",
                user_prompt="user",
            )
        )
        raise AssertionError("expected ProviderNotImplementedError")
    except ProviderNotImplementedError:
        pass


def test_prompt_renderer_extract_and_render() -> None:
    vars_found = extract_variables("Hello {{topic}} — {{audience}}")
    assert vars_found == ["topic", "audience"]
    rendered = render_template(
        "Topic: {{topic}}",
        {"topic": "Mars"},
    )
    assert rendered == "Topic: Mars"


def test_retry_policy_limits() -> None:
    assert decide_retry(current_retries=0, error_message="timeout").should_retry
    assert not decide_retry(current_retries=3, error_message="timeout").should_retry
    assert not decide_retry(
        current_retries=0, error_message="invalid prompt"
    ).should_retry


def test_list_providers_seeds_catalog(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session)
    headers = _auth_header(owner)
    response = client.get("/ai/providers", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    codes = {item["code"] for item in body}
    assert {
        "openai",
        "anthropic",
        "gemini",
        "openrouter",
        "azure_openai",
        "ollama",
    }.issubset(codes)
    for item in body:
        assert "encrypted_api_key" not in item
        assert item["has_credentials"] is False

    models = client.get("/ai/models", headers=headers)
    assert models.status_code == 200
    assert len(models.json()) >= 6


def test_credentials_encrypted_never_returned(
    client: TestClient,
    db_session: Session,
    monkeypatch,
) -> None:
    _enable_credentials_key(monkeypatch)
    owner = _owner(db_session, "owner-creds@example.com")
    headers = _auth_header(owner)

    providers = client.get("/ai/providers", headers=headers).json()
    openai = next(item for item in providers if item["code"] == "openai")

    set_resp = client.post(
        f"/ai/providers/{openai['id']}/credentials",
        headers=headers,
        json={"api_key": "sk-test-secret-value"},
    )
    assert set_resp.status_code == 200, set_resp.text
    body = set_resp.json()
    assert body["has_credentials"] is True
    assert "api_key" not in body
    assert "encrypted_api_key" not in body
    assert "sk-test" not in set_resp.text

    row = db_session.get(AiProvider, openai["id"])
    assert row is not None
    assert row.encrypted_api_key is not None
    assert "sk-test-secret-value" not in row.encrypted_api_key
    assert decrypt_secret(row.encrypted_api_key) == "sk-test-secret-value"

    audit = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_AI_PROVIDER_CREDENTIALS_SET)
    ).all()
    assert audit
    for event in audit:
        meta = event.event_metadata or {}
        assert "api_key" not in meta
        assert "sk-test" not in str(meta)

    clear = client.delete(
        f"/ai/providers/{openai['id']}/credentials",
        headers=headers,
    )
    assert clear.status_code == 204


def test_prompt_versioning_immutable(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-prompt@example.com")
    headers = _auth_header(owner)

    created = client.post(
        "/ai/prompts",
        headers=headers,
        json={
            "name": "Discovery Brief",
            "description": "Foundation prompt",
            "purpose": "discovery_brief",
            "system_prompt": "You are a research assistant.",
            "user_template": "Topic: {{topic}}\nAudience: {{audience}}",
            "variables": ["topic", "audience"],
        },
    )
    assert created.status_code == 201, created.text
    prompt = created.json()
    assert prompt["status"] == "active"
    assert prompt["active_version"]["version_number"] == 1

    v2 = client.post(
        f"/ai/prompts/{prompt['id']}/versions",
        headers=headers,
        json={
            "system_prompt": "You are a senior research assistant.",
            "user_template": "Topic: {{topic}}\nTone: {{tone}}",
            "variables": ["topic", "tone"],
        },
    )
    assert v2.status_code == 201, v2.text
    assert v2.json()["version_number"] == 2
    assert v2.json()["status"] == "draft"

    activate = client.post(
        f"/ai/prompts/{prompt['id']}/versions/{v2.json()['id']}/activate",
        headers=headers,
    )
    assert activate.status_code == 200, activate.text
    assert activate.json()["active_version_id"] == v2.json()["id"]

    versions = client.get(
        f"/ai/prompts/{prompt['id']}/versions",
        headers=headers,
    ).json()
    assert len(versions) == 2
    by_num = {item["version_number"]: item for item in versions}
    assert by_num[1]["system_prompt"] == "You are a research assistant."
    assert by_num[2]["status"] == "active"
    assert by_num[1]["status"] == "superseded"

    audits = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_AI_PROMPT_CREATED)
    ).all()
    assert audits


def test_job_queue_and_cancel_without_generation(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-jobs@example.com")
    headers = _auth_header(owner)

    prompt = client.post(
        "/ai/prompts",
        headers=headers,
        json={
            "name": "Script Spine",
            "purpose": "story_spine",
            "system_prompt": "Outline a story.",
            "user_template": "Topic: {{topic}}",
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
            "input_variables": {"topic": "Black holes"},
        },
    )
    assert job.status_code == 201, job.text
    body = job.json()
    assert body["status"] == "queued"
    assert body["error_message"] is None

    gens = client.get("/ai/generations", headers=headers)
    assert gens.status_code == 200
    assert gens.json()["total"] == 0

    cancelled = client.post(
        f"/ai/jobs/{body['id']}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    actions = {
        row.action
        for row in db_session.scalars(
            select(AuditLog).where(
                AuditLog.action.in_([ACTION_AI_JOB_QUEUED, ACTION_AI_JOB_CANCELLED])
            )
        ).all()
    }
    assert ACTION_AI_JOB_QUEUED in actions
    assert ACTION_AI_JOB_CANCELLED in actions


def test_ai_settings_update(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-settings@example.com")
    headers = _auth_header(owner)
    models = client.get("/ai/models", headers=headers).json()
    model_id = models[0]["id"]

    updated = client.put(
        "/ai/settings",
        headers=headers,
        json={
            "default_model_id": model_id,
            "default_temperature": 0.4,
            "default_max_tokens": 1024,
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["default_model_id"] == model_id
    assert updated.json()["default_temperature"] == 0.4

    audits = db_session.scalars(
        select(AuditLog).where(AuditLog.action == ACTION_AI_SETTINGS_CHANGED)
    ).all()
    assert audits


def test_ai_rbac_permissions(
    client: TestClient,
    db_session: Session,
) -> None:
    reviewer = _role_user(db_session, "reviewer-ai@example.com", "Reviewer")
    headers = _auth_header(reviewer)

    assert client.get("/ai/providers", headers=headers).status_code == 200
    assert (
        client.post(
            "/ai/prompts",
            headers=headers,
            json={
                "name": "Blocked",
                "system_prompt": "x",
                "user_template": "y",
                "variables": [],
            },
        ).status_code
        == 403
    )


def test_undeclared_prompt_variables_rejected(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = _owner(db_session, "owner-vars@example.com")
    headers = _auth_header(owner)
    response = client.post(
        "/ai/prompts",
        headers=headers,
        json={
            "name": "Bad vars",
            "system_prompt": "Use {{topic}}",
            "user_template": "Also {{missing_var}}",
            "variables": ["topic"],
        },
    )
    assert response.status_code == 422
