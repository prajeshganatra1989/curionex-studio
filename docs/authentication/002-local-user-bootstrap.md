# Local User Bootstrap

How to create the first Curionex Studio user safely on a developer machine.

## Prerequisites

1. PostgreSQL running with database `curionex_studio`
2. `backend/.env` configured (`DATABASE_URL`, `JWT_SECRET_KEY`, …)
3. Migrations applied: `alembic upgrade head`
4. Virtualenv activated

```bash
cd backend
source .venv/bin/activate
cp .env.example .env   # if needed — edit with real local values
alembic upgrade head
```

## Create a user (CLI)

Passwords are prompted interactively and **never printed**.

```bash
cd backend
source .venv/bin/activate
python -m app.cli.create_user \
  --email you@example.com \
  --first-name Your \
  --last-name Name
```

You will be prompted for:

- Password
- Confirm password

On success the CLI prints only the email and user id.

## Verify authentication

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Login:

```bash
curl -s http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"YOUR_PASSWORD"}'
```

Use the returned `access_token`:

```bash
curl -s http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

## Security notes

- Do not commit `.env` or real passwords
- Do not put passwords in shell history if avoidable (CLI uses `getpass`)
- Do not share JWT secrets
- There is no public registration endpoint in M2B
