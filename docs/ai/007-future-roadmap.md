# AI Future Roadmap

Planned after AI Foundation (v0.16.0):

1. **Live provider adapters** — OpenAI, Anthropic, Gemini, OpenRouter, Azure OpenAI, Ollama
2. **Job worker** — dequeue `queued` jobs, call adapters, write `ai_generations` + logs
3. **Knowledge Pack generation** — research sections from prompts
4. **Discovery Brief / Story Spine / Master Script** — workflow-aware generation into Script Workspace
5. **Title / description / thumbnail / SEO** — metadata packs tied to Content Versions
6. **Publishing automation** — only after Approval

Constraints that stay true:

- Prompt versions remain immutable references on every generation
- Production workflow (Research → Script → Version → Review → Approval) is never bypassed
- Credentials remain encrypted and never leave the backend
