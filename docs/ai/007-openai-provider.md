# OpenAI Provider (v0.17.0)

## SDK

Direct dependency: `openai==2.52.0` (official Python SDK).

All OpenAI traffic stays on the backend. The frontend never holds API keys or calls OpenAI.

## Responses API

Adapter: `app/ai/providers/openai_provider.py` (`OpenAIProvider`).

- Creates `OpenAI(api_key=..., base_url=...)` from decrypted credentials
- Calls `client.responses.create(...)`
- Structured drafts use `text.format` with `type: json_schema` (strict)
- Fallback for models without structured support: `json_object` + server-side validation

## Normalization

SDK response objects never leave the adapter. Results are mapped to `GenerationResult`:

- `output_text`, `structured_output`
- `tokens_input` / `tokens_output` / `tokens_total`
- `provider_request_id`, `model_identifier`, `latency_ms`, `raw_status`
- `provider_metadata` (sanitized)

## Model selection

Business logic never hard-codes model IDs. Jobs use the selected `AiModel.code` from the database. Knowledge Pack drafts require an **active OpenAI** model.

## Errors and retries

| Error | Retryable |
|-------|-----------|
| Rate limit / timeout / connection | Yes |
| Auth / bad request / config | No |
| Malformed structured output | No |

Retries use `decide_retry` + bounded exponential backoff with jitter inside `job_executor`.

## Credentials

Stored encrypted via `AI_CREDENTIALS_KEY` (Fernet). Decrypt only at call time inside the executor/adapter path. Never logged or returned to clients.
