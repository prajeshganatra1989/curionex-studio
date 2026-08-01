# Frontend Architecture

## Framework

- **Next.js 15** App Router
- **React 19** + **TypeScript**
- **Tailwind CSS v4** design tokens via CSS variables
- **TanStack Query** for async dashboard data
- **React Hook Form** + **Zod** for login validation
- **Lucide** icons
- **Vitest** + **React Testing Library**

## Organization

```
frontend/src/
  app/                 # routes (App Router)
  components/          # UI, layout, dashboard, auth, brand
  lib/api/             # typed API client
  lib/auth/            # token store + AuthProvider
  lib/dashboard/       # typed dashboard models + data adapter
  providers/           # Query + Auth providers
  __tests__/           # Vitest suites
```

## API client

`createApiClient()` centralizes:

- `NEXT_PUBLIC_API_BASE_URL`
- Bearer token attachment
- error normalization (`ApiError`)
- 401 handling hook

Do not call `fetch` ad hoc from feature components.

## Auth state

`AuthProvider` bootstraps from `tokenStore`, loads `GET /auth/me`, and exposes
`login` / `logout`. Route guards + middleware protect authenticated areas.

## Forms

Login uses React Hook Form with a Zod schema. Validation messages are inline and
accessible.

## Testing

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```
