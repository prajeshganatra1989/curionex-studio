# SQLAlchemy and Alembic

How Curionex Studio’s ORM and migration layers fit together.

## Architecture

```text
FastAPI routes / services / repositories
            ↓
   get_db() session dependency
            ↓
        SQLAlchemy 2.x
            ↓
   PostgreSQL (psycopg 3)
```

```text
SQLAlchemy models (subclass Base)
            ↓
      Base.metadata
            ↓
   Alembic autogenerate / revisions
            ↓
     PostgreSQL schema
```

## Key modules

| Module | Responsibility |
|--------|----------------|
| `app/core/config.py` | Loads `DATABASE_URL` from environment / `.env` |
| `app/db/base.py` | Declarative `Base` for all ORM models |
| `app/db/session.py` | Engine, `SessionLocal`, `get_db()`, connectivity probe |
| `alembic/env.py` | Migration runtime; reads settings + `Base.metadata` |
| `alembic/versions/` | Ordered migration scripts |

## SQLAlchemy Base

```python
from app.db.base import Base

class Example(Base):
    __tablename__ = "examples"
    # ...
```

Rules:

- Every ORM model subclasses `Base`.
- No business models in Milestone 2A — the Base is ready for later milestones.
- Import new model modules from `alembic/env.py` (or `app.models`) so
  autogenerate can see them.

## Sessions and dependency injection

`get_db()` yields a **request-scoped** session and always closes it:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

def list_items(db: Session = Depends(get_db)):
    ...
```

Do **not**:

- Keep a global long-lived `Session` on the module
- Share one session across concurrent requests
- Leave sessions open after the request ends

The engine uses `pool_pre_ping=True` so stale connections are detected.

## Alembic responsibility

Alembic owns **schema change history**.

- Application code must **not** call `Base.metadata.create_all()` for production schema.
- Schema changes ship as reviewed migration files.
- `DATABASE_URL` comes from application settings — not hard-coded credentials in `alembic.ini`.

## Recommended migration workflow

1. Change / add a SQLAlchemy model under `app/models/`.
2. Generate a migration: `alembic revision --autogenerate -m "describe_change"`.
3. **Review** the generated script (autogenerate is a helper, not gospel).
4. Run locally: `alembic upgrade head`.
5. Run tests: `ruff check .` and `pytest`.
6. Commit **model + migration together**.
7. Open a PR into `main`.
8. CI runs lint + tests.
9. Merge only when checks pass.

## Common commands

From `backend/` with the venv active:

```bash
alembic revision --autogenerate -m "add_users"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

## What developers must NOT do

- Do not manually create application tables in `psql` and skip Alembic.
- Do not edit old migrations that already ran on shared databases — add a new revision.
- Do not put real database passwords in source control.
- Do not store API secrets in the database settings tables (see architecture docs).
- Do not implement User/Role/Project models in this foundation milestone.
- Do not make the default `/health` endpoint depend on PostgreSQL.
- Do not use Docker for local database setup in this project phase.

## CI note

GitHub Actions currently runs Ruff + pytest **without** a PostgreSQL service.

- Unit tests mock or avoid live DB connections.
- A future CI enhancement may add a PostgreSQL service container or managed job
  for migration + `/health/db` integration checks.
- Until then, developers verify migrations against local PostgreSQL.

## Related docs

- [001-database-architecture.md](./001-database-architecture.md) — target schema
- [002-entity-relationship.md](./002-entity-relationship.md) — ER diagram
- [003-local-postgresql.md](./003-local-postgresql.md) — local setup
- [../architecture/002-database-decisions.md](../architecture/002-database-decisions.md) — design rationale
