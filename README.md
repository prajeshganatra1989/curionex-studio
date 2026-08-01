# Curionex Studio

Curionex Studio manages the complete content production lifecycle for premium educational scripts.

## Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS

## Local development

### Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

API: http://127.0.0.1:8000

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

## Current milestone

`v0.10.0` backend workflow + Frontend Sprint 1 foundation (login, shell, dashboard).
