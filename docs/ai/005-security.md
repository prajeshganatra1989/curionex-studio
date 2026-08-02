# AI Credential Security

## Rules

1. API keys are **never** stored in plaintext.
2. API keys are **never** logged or placed in audit metadata.
3. API keys are **never** returned to the frontend (responses expose `has_credentials` only).
4. Encryption key lives in environment: `AI_CREDENTIALS_KEY`.

## Implementation

- Library: Fernet (`cryptography`)
- Helper: `app/ai/credentials.py` — `encrypt_secret` / `decrypt_secret`
- Storage column: `ai_providers.encrypted_api_key` (ciphertext text)
- Audit service already bans keys such as `api_key`, `secret`, `credential`

## Setup

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set in `.env`:

```env
AI_CREDENTIALS_KEY=<url-safe-base64-32-byte-key>
```

If unset, credential writes fail with a clear configuration error (HTTP 503).

## Frontend

Settings UI can set/clear credentials. Responses never include the secret — only `has_credentials: true|false`.
