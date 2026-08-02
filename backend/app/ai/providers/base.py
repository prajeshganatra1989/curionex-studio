"""AI provider abstraction — interfaces only (no live API calls in v0.16.0)."""

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
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationResult:
    """Normalized provider response (unused until providers are implemented)."""

    output_text: str
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: int | None = None
    reasoning_metadata: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class AIProvider(ABC):
    """Provider adapter contract.

    Concrete adapters for OpenAI, Anthropic, Gemini, OpenRouter, Azure OpenAI,
    and Ollama will implement ``generate``. Foundation sprint registers stubs
    that raise ``ProviderNotImplementedError`` so jobs can queue safely without
    calling external APIs.
    """

    code: str
    display_name: str

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Execute a model generation. Must not be called until Sprint 5+."""

    def validate_credentials(self, api_key: str | None, base_url: str | None) -> None:
        """Optional credential shape check (no network I/O)."""
        return None
