# Projects UI

## Routes

- `/projects` — live project list
- Query params: `search`, `status`, `category_id`, `tag_id`, `page`

## List behaviour

Uses `GET /projects` with backend filtering and pagination (`items`, `page`,
`page_size`, `total`). Search is debounced (~350ms) before writing the URL and
refetching. Changing filters resets `page` to `1`.

Each card shows CRX code, name, description preview, status, category, tags,
and updated time. The overflow menu supports Open and Archive only.

## Creation and editing

Create opens an accessible modal (`React Hook Form` + Zod):

- name, description, status (`draft` | `active`)
- category picker (search + inline create via `POST /categories`)
- multi-tag picker (chips + inline create via `POST /tags`)

Project codes are server-generated (`CRX-####`) and never entered manually.

On success: toast, invalidate project queries, navigate to Project Home.

Edit is available from Project Home (PATCH). Project code is read-only.

## Archiving

Archive uses `DELETE /projects/{id}` (soft archive). Confirmation explains that
content is preserved. After success, list/detail queries refresh. Archived
projects remain visible when the status filter is `archived`.

## API hooks

`src/lib/projects/hooks.ts` — stable keys under `projectKeys` / `taxonomyKeys`:

- `useProjects`, `useProject`
- `useCreateProject`, `useUpdateProject`, `useArchiveProject`
- `useCategories`, `useCreateCategory`, `useTags`, `useCreateTag`

API functions live in `src/lib/api/projects.ts` with types in
`src/lib/api/types.ts`.

## Authorization

Backend remains the source of truth. UI shows:

- 401 → existing auth logout/redirect
- 403 → restricted empty state
- 404 → not-found empty state

No role-name checks (`if role === "Owner"`).

## Empty / loading / error

- Skeleton cards while loading
- Branded empty state when no projects exist
- Filter-empty state with reset
- Safe error message + retry (never raw JSON)
