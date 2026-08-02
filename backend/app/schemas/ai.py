"""AI foundation API schemas — providers, prompts, jobs, generations, settings."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ai.constants import PROMPT_STATUSES


class AiProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    is_active: bool
    base_url: str | None
    has_credentials: bool
    created_at: datetime
    updated_at: datetime


class AiProviderUpdate(BaseModel):
    is_active: bool | None = None
    base_url: str | None = Field(default=None, max_length=500)

    @field_validator("base_url")
    @classmethod
    def strip_base_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AiProviderCredentials(BaseModel):
    api_key: str = Field(min_length=1, max_length=4000)

    @field_validator("api_key")
    @classmethod
    def strip_api_key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("api_key must not be empty")
        return cleaned


class AiModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    code: str
    name: str
    context_window: int | None
    supports_reasoning: bool
    supports_streaming: bool
    is_active: bool
    is_default: bool
    pricing_input_per_1k: float | None
    pricing_output_per_1k: float | None


class AiModelUpdate(BaseModel):
    is_active: bool | None = None
    is_default: bool | None = None


class AiPromptVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prompt_id: UUID
    version_number: int
    system_prompt: str
    user_template: str
    variables: list[str]
    status: str
    created_by: UUID
    created_at: datetime


class AiPromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    purpose: str | None
    status: str
    owner_id: UUID
    active_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    active_version: AiPromptVersionResponse | None = None


class AiPromptListResponse(BaseModel):
    items: list[AiPromptResponse]
    page: int
    page_size: int
    total: int


class AiPromptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    purpose: str | None = Field(default=None, max_length=120)
    system_prompt: str = Field(min_length=1, max_length=100000)
    user_template: str = Field(min_length=1, max_length=100000)
    variables: list[str] = Field(default_factory=list)

    @field_validator("name", "system_prompt", "user_template")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("description", "purpose")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("variables")
    @classmethod
    def normalize_variables(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            name = str(item).strip()
            if not name:
                raise ValueError("variable names must not be empty")
            if name not in seen:
                seen.add(name)
                cleaned.append(name)
        return cleaned


class AiPromptUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    purpose: str | None = Field(default=None, max_length=120)
    status: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("description", "purpose")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if cleaned not in PROMPT_STATUSES:
            raise ValueError(
                "status must be one of: " + ", ".join(sorted(PROMPT_STATUSES))
            )
        return cleaned


class AiPromptVersionCreate(BaseModel):
    system_prompt: str = Field(min_length=1, max_length=100000)
    user_template: str = Field(min_length=1, max_length=100000)
    variables: list[str] = Field(default_factory=list)

    @field_validator("system_prompt", "user_template")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("variables")
    @classmethod
    def normalize_variables(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            name = str(item).strip()
            if not name:
                raise ValueError("variable names must not be empty")
            if name not in seen:
                seen.add(name)
                cleaned.append(name)
        return cleaned


class AiJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    requested_by: UUID
    prompt_version_id: UUID
    model_id: UUID
    input_variables: dict[str, Any]
    purpose: str | None = None
    knowledge_pack_id: UUID | None = None
    project_id: UUID | None = None
    script_id: UUID | None = None
    document_type: str | None = None
    idempotency_key: str | None = None
    cancel_requested: bool = False
    generation_id: UUID | None = None
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    retries: int
    error_message: str | None
    created_at: datetime


class AiJobListResponse(BaseModel):
    items: list[AiJobResponse]
    page: int
    page_size: int
    total: int


class AiJobCreate(BaseModel):
    prompt_id: UUID
    model_id: UUID
    input_variables: dict[str, str] = Field(default_factory=dict)


class AiGenerationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    prompt_version_id: UUID
    model_id: UUID
    provider_id: UUID
    input_variables: dict[str, Any]
    output_text: str | None
    structured_output: dict[str, Any] | None = None
    purpose: str | None = None
    knowledge_pack_id: UUID | None = None
    project_id: UUID | None = None
    script_id: UUID | None = None
    document_type: str | None = None
    tokens_input: int | None
    tokens_output: int | None
    tokens_total: int | None = None
    cost_usd: float | None
    latency_ms: int | None
    provider_request_id: str | None = None
    model_identifier: str | None = None
    temperature: float | None
    seed: int | None
    applied_sections: list[str] = Field(default_factory=list)
    applied_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    input_fingerprint: dict[str, Any] | None = None
    stale_input: bool | None = None
    created_at: datetime


class AiGenerationListResponse(BaseModel):
    items: list[AiGenerationResponse]
    page: int
    page_size: int
    total: int


class KnowledgePackAiDraftCreate(BaseModel):
    model_id: UUID | None = None
    target_audience: str = Field(default="general learners", max_length=200)
    language: str = Field(default="en", max_length=32)
    desired_depth: str = Field(default="standard", max_length=64)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("target_audience", "language", "desired_depth")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("idempotency_key")
    @classmethod
    def strip_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class KnowledgePackAiDraftApply(BaseModel):
    sections: list[str] = Field(min_length=1)
    conflict_strategy: str = Field(default="reject_if_non_empty")

    @field_validator("conflict_strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        allowed = {
            "reject_if_non_empty",
            "replace_selected",
            "append_selected",
        }
        cleaned = value.strip()
        if cleaned not in allowed:
            raise ValueError(
                "conflict_strategy must be one of: " + ", ".join(sorted(allowed))
            )
        return cleaned


class KnowledgePackAiDraftApplyResponse(BaseModel):
    knowledge_pack: dict[str, Any]
    generation_id: UUID
    applied_sections: list[str]
    conflict_strategy: str


class AiSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    default_model_id: UUID | None
    default_temperature: float
    default_max_tokens: int
    brand_voice: str | None = None
    quality_requirements: str | None = None
    default_target_duration_seconds: int = 60
    default_target_words_per_minute: int = 150


class AiSettingsUpdate(BaseModel):
    default_model_id: UUID | None = None
    default_temperature: float | None = Field(default=None, ge=0, le=2)
    default_max_tokens: int | None = Field(default=None, ge=1, le=128000)
    brand_voice: str | None = Field(default=None, max_length=4000)
    quality_requirements: str | None = Field(default=None, max_length=8000)
    default_target_duration_seconds: int | None = Field(default=None, ge=15, le=300)
    default_target_words_per_minute: int | None = Field(default=None, ge=80, le=220)


class ScriptAiDraftCreate(BaseModel):
    model_id: UUID | None = None
    language: str = Field(default="English", max_length=64)
    tone: str = Field(default="curious, cinematic, clear", max_length=200)
    target_duration_seconds: int | None = Field(default=None, ge=15, le=300)
    target_words_per_minute: int | None = Field(default=None, ge=80, le=220)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("language", "tone")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("idempotency_key")
    @classmethod
    def strip_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ScriptAiDraftApply(BaseModel):
    conflict_strategy: str = Field(default="reject_if_non_empty")

    @field_validator("conflict_strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        allowed = {"reject_if_non_empty", "replace", "append"}
        cleaned = value.strip()
        if cleaned not in allowed:
            raise ValueError(
                "conflict_strategy must be one of: " + ", ".join(sorted(allowed))
            )
        return cleaned


class ScriptAiDraftApplyResponse(BaseModel):
    document: dict[str, Any]
    generation_id: UUID
    conflict_strategy: str
    stale_input: bool


class ScriptAiPrerequisitesResponse(BaseModel):
    document_type: str
    ready: bool
    missing: list[str] = Field(default_factory=list)


class ScriptQualityReviewCreate(BaseModel):
    model_id: UUID | None = None
    language: str = Field(default="English", max_length=64)
    target_duration_seconds: int | None = Field(default=None, ge=15, le=300)
    target_words_per_minute: int | None = Field(default=None, ge=80, le=220)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("language")
    @classmethod
    def strip_language(cls, value: str) -> str:
        return value.strip()

    @field_validator("idempotency_key")
    @classmethod
    def strip_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ScriptQualitySuggestionApply(BaseModel):
    strategy: str = Field(default="replace_excerpt")

    @field_validator("strategy")
    @classmethod
    def validate_strategy(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned != "replace_excerpt":
            raise ValueError("strategy must be replace_excerpt")
        return cleaned


class ScriptQualitySuggestionApplyResponse(BaseModel):
    document: dict[str, Any]
    generation_id: UUID
    issue_id: str
    strategy: str
    stale_input: bool
