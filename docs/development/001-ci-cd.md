# Continuous Integration

## Purpose

GitHub Actions CI runs automated quality checks on the Curionex Studio backend so broken code is caught before it lands on `main`.

Current CI covers:

- Ruff linting
- pytest (full backend suite)

CI does **not** yet deploy, migrate databases, build Docker images, or run AI/n8n workflows.

## When GitHub Actions runs

Workflow: `.github/workflows/backend-tests.yml`

Triggers:

1. Pull requests targeting `main`
2. Pushes to `main`

## Local commands (run before opening a PR)

```bash
cd backend
source .venv/bin/activate
ruff check .
pytest
```

Install or refresh dependencies if needed:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

## Branch expectations

- Do feature and bugfix work on dedicated branches (`feature/*`, `bugfix/*`).
- Open a pull request into `main`.
- Keep the branch up to date with `main` when practical.

See [002-git-workflow.md](./002-git-workflow.md).

## Pull request expectations

Before requesting review:

1. Run `ruff check .` and `pytest` locally.
2. Keep the PR focused on one change set.
3. Ensure CI is green (or explain any infrastructure failure).

## What happens when CI fails

- The workflow fails and the PR should not be merged.
- Fix lint or test failures on the feature branch.
- Push again; CI re-runs automatically.
- Do not bypass failing checks.

Recommended branch protection settings: [004-github-branch-protection.md](./004-github-branch-protection.md).
