"""Stub provider adapters — registered but never call external APIs."""

from __future__ import annotations

from app.ai.providers.base import (
    AIProvider,
    GenerationRequest,
    GenerationResult,
    ProviderNotImplementedError,
)


class StubProvider(AIProvider):
    def __init__(self, code: str, display_name: str) -> None:
        self.code = code
        self.display_name = display_name

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderNotImplementedError(
            f"Provider '{self.code}' is registered but live generation is not "
            "enabled in the AI Foundation sprint (v0.16.0)."
        )


def build_stub_providers() -> dict[str, AIProvider]:
    from app.ai.constants import (
        PROVIDER_ANTHROPIC,
        PROVIDER_AZURE_OPENAI,
        PROVIDER_GEMINI,
        PROVIDER_OLLAMA,
        PROVIDER_OPENAI,
        PROVIDER_OPENROUTER,
    )

    specs = (
        (PROVIDER_OPENAI, "OpenAI"),
        (PROVIDER_ANTHROPIC, "Anthropic"),
        (PROVIDER_GEMINI, "Google Gemini"),
        (PROVIDER_OPENROUTER, "OpenRouter"),
        (PROVIDER_AZURE_OPENAI, "Azure OpenAI"),
        (PROVIDER_OLLAMA, "Ollama"),
    )
    return {code: StubProvider(code, name) for code, name in specs}
