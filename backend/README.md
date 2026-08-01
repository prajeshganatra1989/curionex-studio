# Curionex Studio Backend

FastAPI API that powers Curionex Studio, a content production management platform.

## Requirements

- Python 3.12.13
- PostgreSQL (for future migrations and data persistence)

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

## Run the API

From `backend/` with the virtual environment activated:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Health endpoint

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "curionex-studio-api"
}
```

## Run tests

From `backend/` with the virtual environment activated:

```bash
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
- Alembic is configured as the migration foundation only. No application tables have been created yet.
- Keep route handlers thin: put business logic in services and persistence in repositories.
- Do not commit `.env` files. Use `.env.example` as the safe template.
