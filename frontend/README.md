# Curionex Studio Frontend

Next.js App Router UI for Curionex Studio.

## Local development

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App: [http://localhost:3000](http://localhost:3000)

Backend (separate terminal):

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

API: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Scripts

- `npm run dev` — development server
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript
- `npm run test` — Vitest
- `npm run build` — production build

## Brand assets

Raster logos live in `public/brand/`. Transparent SVG/PNG replacements can swap
in later without changing `BrandLogo` / `BrandMark` components.
