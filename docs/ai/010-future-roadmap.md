# AI Future Roadmap

Completed in v0.17.0:

1. Live OpenAI Responses adapter
2. Knowledge Pack draft generation + selective apply

Still planned:

1. Live adapters for Anthropic, Gemini, OpenRouter, Azure OpenAI, Ollama
2. Async job worker / queue (beyond sync execution)
3. Discovery Brief / Story Spine / Master Script generation
4. Title / description / thumbnail / SEO packs tied to Content Versions
5. Publishing automation — only after Approval

Constraints that stay true:

- Prompt versions remain immutable references on every generation
- Production workflow (Research → Script → Version → Review → Approval) is never bypassed
- Credentials remain encrypted and never leave the backend
- Sources from AI drafts remain unverified until humans check them
