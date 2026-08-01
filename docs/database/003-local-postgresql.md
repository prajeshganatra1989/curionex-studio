# Local PostgreSQL Setup

How to run PostgreSQL for Curionex Studio on a developer machine (no Docker).

## Prerequisites

- PostgreSQL installed and running locally
- Backend virtual environment at `backend/.venv`
- Python 3.12.13

Installation varies by OS (Homebrew, Postgres.app, apt, etc.). Any supported
PostgreSQL 14+ instance is fine.

## Create the database

Using `psql` (adjust the superuser if yours differs):

```bash
psql -U postgres -h localhost
```

Then:

```sql
CREATE DATABASE curionex_studio;
```

Optional dedicated role:

```sql
CREATE USER curionex WITH PASSWORD 'choose_a_local_password';
GRANT ALL PRIVILEGES ON DATABASE curionex_studio TO curionex;
```

On PostgreSQL 15+, you may also need schema privileges inside the database:

```sql
\c curionex_studio
GRANT ALL ON SCHEMA public TO curionex;
```

## Configure DATABASE_URL

From `backend/`:

```bash
cp .env.example .env
```

Edit `.env` with your real local credentials (never commit `.env`):

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/curionex_studio
```

Driver note: the URL scheme must be `postgresql+psycopg://` (psycopg 3).

## Activate the environment and install deps

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Alembic migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Useful commands:

| Command | Purpose |
|---------|---------|
| `alembic current` | Show applied revision |
| `alembic history` | Show revision history |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one revision |

The initial revision (`database_foundation`) is intentionally empty — it only
proves Alembic is wired correctly. Application tables arrive in later milestones.

## Start the API and verify database health

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Process health (no database required):

```bash
curl http://127.0.0.1:8000/health
```

Database connectivity:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected success:

```json
{"status":"ok","database":"connected"}
```

If PostgreSQL is down, `/health/db` returns HTTP 503 with a safe error payload
(no passwords or connection strings).

## Automated tests vs PostgreSQL

`pytest` does **not** require a live PostgreSQL instance.

- `GET /health` and database foundation unit tests use mocks/imports only.
- Live `/health/db` and `alembic upgrade head` against a real server are
  **manual developer checks** today.
- Adding PostgreSQL to GitHub Actions CI is a future enhancement — do not make
  CI fragile by requiring an unavailable database.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `connection refused` | PostgreSQL not running | Start the local Postgres service |
| `password authentication failed` | Bad user/password in `.env` | Fix `DATABASE_URL` |
| `database "curionex_studio" does not exist` | DB not created | `CREATE DATABASE curionex_studio;` |
| `No module named psycopg` | Missing deps / wrong venv | `pip install -r requirements.txt` inside `.venv` |
| Alembic can't import `app` | Wrong working directory | Run Alembic from `backend/` |
| `/health` OK but `/health/db` 503 | App up, DB unreachable | Check Postgres + `DATABASE_URL` |

## Security reminders

- Never commit `.env` or real credentials.
- Keep placeholders only in `.env.example`.
- Do not log full `DATABASE_URL` values in application code.
