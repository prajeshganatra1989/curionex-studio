# Curionex Studio Backend

FastAPI API that powers Curionex Studio, a content production management platform.

## Requirements

- Python 3.12.13
- PostgreSQL (local install; see `docs/database/003-local-postgresql.md`)

## Setup

From the `backend/` directory, activate the virtual environment:

```bash
source .venv/bin/activate
```

Copy the example environment file and adjust values as needed:

```bash
cp .env.example .env
```

Dependencies are listed in `requirements.txt`. With the venv active:

```bash
pip install -r requirements.txt
```

## Database

Configure `DATABASE_URL` in `.env`, create the `curionex_studio` database, then:

```bash
alembic upgrade head
```

Full local PostgreSQL instructions: [`docs/database/003-local-postgresql.md`](../docs/database/003-local-postgresql.md)

SQLAlchemy / Alembic workflow: [`docs/database/004-sqlalchemy-alembic.md`](../docs/database/004-sqlalchemy-alembic.md)

## Run the API

From `backend/` with the virtual environment activated:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Health endpoints

```http
GET /health
```

Process health (does not require PostgreSQL):

```json
{
  "status": "ok",
  "service": "curionex-studio-api"
}
```

```http
GET /health/db
```

Database connectivity probe:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## Authentication

Configure `JWT_SECRET_KEY` in `.env` (see `.env.example`).

Create the first local user (password prompted securely):

```bash
python -m app.cli.create_user \
  --email you@example.com \
  --first-name Your \
  --last-name Name
```

```http
POST /auth/login
GET  /auth/me
```

Docs: [`docs/authentication/`](../docs/authentication/)

## Run tests / lint

```bash
ruff check .
pytest
```

## Project layout

| Path | Role |
|------|------|
| `app/api/` | HTTP routes and API router |
| `app/core/` | Settings and shared config |
| `app/db/` | Engine, session, declarative base |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic schemas |
| `app/services/` | Business logic |
| `app/repositories/` | Data access |
| `alembic/` | Database migrations |

## Development notes

- Run natively on the developer machine; Docker is not used.
- The initial Alembic revision is empty (foundation only). Application tables arrive in later milestones.
- Keep route handlers thin: put business logic in services and persistence in repositories.
- Do not commit `.env` files. Use `.env.example` as the safe template.
