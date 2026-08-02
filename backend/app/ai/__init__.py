"""AI package — provider registry, prompts, jobs (no live generation)."""

from app.ai.providers import get_provider, get_provider_registry, list_provider_codes

__all__ = [
    "get_provider",
    "get_provider_registry",
    "list_provider_codes",
]
