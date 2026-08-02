"""Provider registry / factory — single place to resolve provider adapters."""

from __future__ import annotations

from app.ai.constants import (
    PROVIDER_ANTHROPIC,
    PROVIDER_AZURE_OPENAI,
    PROVIDER_GEMINI,
    PROVIDER_OLLAMA,
    PROVIDER_OPENAI,
    PROVIDER_OPENROUTER,
)
from app.ai.providers.base import AIProvider, ProviderNotImplementedError
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.providers.stubs import StubProvider

_REGISTRY: dict[str, AIProvider] | None = None


def build_provider_registry() -> dict[str, AIProvider]:
    """Register live OpenAI adapter; other providers remain stubs."""
    registry: dict[str, AIProvider] = {
        PROVIDER_OPENAI: OpenAIProvider(),
        PROVIDER_ANTHROPIC: StubProvider(PROVIDER_ANTHROPIC, "Anthropic"),
        PROVIDER_GEMINI: StubProvider(PROVIDER_GEMINI, "Google Gemini"),
        PROVIDER_OPENROUTER: StubProvider(PROVIDER_OPENROUTER, "OpenRouter"),
        PROVIDER_AZURE_OPENAI: StubProvider(PROVIDER_AZURE_OPENAI, "Azure OpenAI"),
        PROVIDER_OLLAMA: StubProvider(PROVIDER_OLLAMA, "Ollama"),
    }
    return registry


def get_provider_registry() -> dict[str, AIProvider]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_provider_registry()
    return _REGISTRY


def get_provider(code: str) -> AIProvider:
    registry = get_provider_registry()
    provider = registry.get(code)
    if provider is None:
        raise ProviderNotImplementedError(f"Unknown AI provider '{code}'.")
    return provider


def list_provider_codes() -> list[str]:
    return sorted(get_provider_registry().keys())


def reset_provider_registry() -> None:
    """Test helper to clear the singleton registry."""
    global _REGISTRY
    _REGISTRY = None
