# Prompt Versioning

Prompts are first-class entities. Edits never overwrite history.

## Entities

- `ai_prompts` — name, description, purpose, status, owner, `active_version_id`
- `ai_prompt_versions` — immutable snapshot: system prompt, user template, variables, version number, status

## Lifecycle

1. Create prompt → version `1` is created and activated.
2. Save edits → **new** version row (`draft`).
3. Activate version → previous active becomes `superseded`; prompt `active_version_id` updates.
4. Future generations reference the exact `prompt_version_id` used.

## Variables

Placeholders use `{{name}}` syntax.

Known examples: `topic`, `research`, `audience`, `facts`, `sources`, `tone`, `length`, `language`.

Validation (`prompt_renderer.py`):

- Declared variables must cover all placeholders in templates.
- Job queueing requires values for every declared variable.
- Rendering substitutes values; missing keys raise `PromptRenderError`.

## Statuses

Prompt: `draft` | `active` | `archived`  
Version: `draft` | `active` | `superseded`
