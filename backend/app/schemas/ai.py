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
    tokens_input: int | None
    tokens_output: int | None
    cost_usd: float | None
    latency_ms: int | None
    temperature: float | None
    seed: int | None
    created_at: datetime


class AiGenerationListResponse(BaseModel):
    items: list[AiGenerationResponse]
    page: int
    page_size: int
    total: int


class AiSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    default_model_id: UUID | None
    default_temperature: float
    default_max_tokens: int


class AiSettingsUpdate(BaseModel):
    default_model_id: UUID | None = None
    default_temperature: float | None = Field(default=None, ge=0, le=2)
    default_max_tokens: int | None = Field(default=None, ge=1, le=128000)
