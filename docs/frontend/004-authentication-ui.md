# Authentication UI

## Flow

1. `POST /auth/login` with email/password
2. Store Bearer access token via `tokenStore`
3. Set non-secret `curionex_auth=1` cookie for middleware redirects
4. `GET /auth/me` loads the signed-in profile
5. Logout clears token + cookie (no backend logout endpoint)

## Route protection

- Middleware redirects unauthenticated users away from app routes
- `RequireAuth` client guard double-checks session bootstrap
- Authenticated users hitting `/login` redirect to `/dashboard`

## Token handling

Backend returns JWT in JSON (`TokenResponse`) and does **not** set HttpOnly cookies.

Sprint 1 approach:

- JWT in `sessionStorage` through `tokenStore` only
- Never log tokens
- Never put tokens in URLs
- Never scatter storage access across components

### Security tradeoff

`sessionStorage` is XSS-readable. Prefer migrating to **HttpOnly Secure cookies**
when the API supports cookie sessions. Until then, keep XSS surface minimal and
centralize token access.

## CORS

Backend `CORS_ORIGINS` is environment-configurable. Wildcard origins never pair
with credentials.
