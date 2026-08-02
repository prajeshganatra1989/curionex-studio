# Curionex Brand Voice

Brand voice and draft quality requirements are **studio settings**, not hard-coded in provider adapters.

## Settings fields

On `ai_settings` (editable via AI Settings API / UI):

| Field | Role |
|-------|------|
| `brand_voice` | Voice guidance injected into script draft prompts |
| `quality_requirements` | Quality bar injected alongside brand voice |
| `default_target_duration_seconds` | Default duration for draft jobs (default 60) |
| `default_target_words_per_minute` | Default WPM for word-count targets (default 150) |

## Defaults

If settings columns are null/empty, `script_draft.py` supplies fallbacks:

- **Brand voice** — curious, clear, cinematic, intelligent, warm, concise, non-sensational, accessible, evidence-conscious, optimized for spoken narration  
- **Quality requirements** — one clear core idea; strong opening; meaningful payoff; factual caution; no invented certainty; no filler; no unsupported quotation; no unnecessary jargon; suitable for spoken English; appropriate for short-form education  

These defaults live next to draft schemas/constants — **not** inside OpenAI (or other) adapter code.

## How they reach the model

`script_ai_service._build_variables` reads settings (or defaults) and passes `brand_voice` and `quality_requirements` as prompt template variables for all three script draft purposes.

The same resolved strings are copied into the input fingerprint `settings_snapshot`, so changing studio voice/quality after a generation can mark that draft stale.

## Adapter boundary

Provider adapters receive already-rendered system/user prompts and structured schemas. They do not embed Curionex voice or quality copy. Changing voice is a settings/prompt concern, not an adapter change.
