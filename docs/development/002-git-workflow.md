# Git Workflow

Curionex Studio uses a simple trunk-based style workflow. No full GitFlow.

```text
main
  ↑
feature/*  or  bugfix/*
  ↑
local development
```

## Rules

1. **Do not develop directly on `main`.**
2. New functionality uses `feature/<short-name>` (example: `feature/health-endpoint`).
3. Bug fixes use `bugfix/<short-name>` (example: `bugfix/login-500`).
4. Open a **pull request into `main`**.
5. **CI must pass** before merge.
6. **Review changes** before merge (even on a small team, a second look helps).
7. **Do not merge failing CI.**
8. Keep commits **focused and meaningful**.

## Typical flow

```bash
git checkout main
git pull origin main
git checkout -b feature/my-change

# ... implement, lint, test ...

git add -A
git commit -m "Describe why this change exists."
git push -u origin HEAD
# Open PR → wait for CI → review → merge
```

## Out of scope (for now)

- Release trains / develop branch
- Hotfix-only branching models
- Automatic version bumps on every merge

Version tags are documented separately in [003-versioning.md](./003-versioning.md).
