"""Provider registry / factory — single place to resolve provider adapters."""

from __future__ import annotations

from app.ai.providers.base import AIProvider, ProviderNotImplementedError
from app.ai.providers.stubs import build_stub_providers

_REGISTRY: dict[str, AIProvider] | None = None


def get_provider_registry() -> dict[str, AIProvider]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = build_stub_providers()
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
