"""AI provider abstraction — normalized request/result contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProviderNotImplementedError(RuntimeError):
    """Raised when a provider adapter has no live implementation yet."""


@dataclass(frozen=True)
class GenerationRequest:
    """Normalized generation request passed to a provider adapter."""

    model_code: str
    system_prompt: str
    user_prompt: str
    temperature: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    # JSON Schema dict for structured Responses API output (optional).
    response_json_schema: dict[str, Any] | None = None
    response_schema_name: str | None = None
    # Model capability hints from AiModel.metadata_json / columns.
    supports_structured_output: bool = True
    supports_temperature: bool = True
    reasoning_effort: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    # Injected by job executor — never logged.
    api_key: str | None = None
    base_url: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    """Provider-neutral generation result (SDK objects never escape adapters)."""

    output_text: str
    structured_output: dict[str, Any] | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    tokens_total: int | None = None
    latency_ms: int | None = None
    provider_request_id: str | None = None
    model_identifier: str | None = None
    raw_status: str | None = None
    retryable: bool = False
    reasoning_metadata: dict[str, Any] | None = None
    provider_metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    """Provider adapter contract."""

    code: str
    display_name: str

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Execute a model generation via the provider SDK."""

    def validate_credentials(self, api_key: str | None, base_url: str | None) -> None:
        """Optional credential shape check (no network I/O by default)."""
        return None
