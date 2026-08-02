# AI Foundation Architecture (v0.16.0)

This sprint builds **infrastructure only**. No live model calls. No content generation.

Future capabilities (Knowledge Packs, Discovery Briefs, Story Spines, Master Scripts, titles, SEO, thumbnails, publishing) plug into this foundation and into the existing production workflow:

```text
Research → Script → Version → Review → Approval
```

AI must **not** bypass Content Versions or Approvals.

## Components

| Layer | Responsibility |
|-------|----------------|
| Providers | Registry/factory of adapter interfaces (stubs in v0.16.0) |
| Models | Catalog of models per provider (context, streaming, pricing) |
| Prompts | First-class prompt entities with immutable versions |
| Jobs | Queued generation requests with lifecycle states |
| Generations | Historical outputs + tokens/cost/latency (empty until live providers) |
| Settings | Non-secret defaults (model, temperature, max tokens) |
| Credentials | Encrypted API keys at rest — never returned to the frontend |

## Module map

```text
backend/app/ai/
  constants.py
  credentials.py
  cost.py
  prompt_renderer.py
  retry.py
  providers/
    base.py          # AIProvider ABC
    stubs.py         # Stub adapters
    __init__.py      # Registry / factory

backend/app/services/ai_service.py
backend/app/api/routes/ai.py
backend/app/models/ai.py
backend/app/schemas/ai.py
```

## Frontend surfaces

- `/ai` — hub
- `/ai/settings` — providers, models, defaults
- `/ai/prompts` — prompt library + editor + versions
- `/ai/jobs` — job monitor
- `/ai/generations` — generation history (empty until Sprint 5+)

## RBAC

| Permission | Use |
|------------|-----|
| `ai.view` | Read providers, models, prompts, jobs, generations, settings |
| `ai.manage` | Update providers/credentials/models/settings |
| `ai.generate` | Queue / cancel jobs |
| `prompt.manage` | Create prompts and versions |

## What this sprint does **not** do

- Call OpenAI, Anthropic, Gemini, OpenRouter, Azure, or Ollama
- Write generated content into scripts or knowledge packs
- Auto-publish or mutate Content Versions
