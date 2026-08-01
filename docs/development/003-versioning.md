# Versioning

Curionex Studio uses **Semantic Versioning**:

```text
MAJOR.MINOR.PATCH
```

Examples:

- `v0.1.0`
- `v0.2.0`
- `v0.2.1`
- `v1.0.0`

## Meaning

| Part | When to bump |
|------|----------------|
| **MAJOR** | Breaking changes (incompatible API or data changes) |
| **MINOR** | New functionality that remains backward compatible |
| **PATCH** | Backward-compatible bug fixes |

## Tags

- Git tags (for example `v0.1.0`) mark **verified milestones**.
- Do **not** create a tag for every commit or every merge.
- Tag deliberately after a known-good state on `main` (tests green, intended scope complete).

## Current stage

The project is in early development (`0.x`). Expect APIs and schemas to evolve. Still use SemVer so milestones stay readable.

Automated release tagging is **not** part of CI yet.
