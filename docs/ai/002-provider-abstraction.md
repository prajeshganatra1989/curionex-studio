# Provider Abstraction

All provider access goes through a single registry.

```python
from app.ai.providers import get_provider

adapter = get_provider("openai")
# adapter.generate(...)  # raises ProviderNotImplementedError in v0.16.0
```

## Contract

`AIProvider` (`app/ai/providers/base.py`) defines:

- `code` / `display_name`
- `generate(GenerationRequest) -> GenerationResult`
- optional `validate_credentials` (no network I/O)

`GenerationRequest` normalizes model code, system/user prompts, temperature, max tokens, seed, and extras.

## Registry

`build_stub_providers()` registers:

- `openai`
- `anthropic`
- `gemini`
- `openrouter`
- `azure_openai`
- `ollama`

Stubs raise `ProviderNotImplementedError`. Live adapters land in later sprints **without** changing call sites.

## Rules

1. Never call HTTP clients from services directly.
2. Never scatter provider-specific branching across the codebase.
3. Resolve adapters only via `get_provider(code)`.
4. Persist provider/model metadata in `ai_providers` / `ai_models`.
