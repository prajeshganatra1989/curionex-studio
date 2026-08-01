# Project Code Generation (M2E)

## Goal

Allocate unique, human-readable project codes such as `CRX-0001` without races under
concurrent project creation.

## Mechanism

1. PostgreSQL sequence `project_code_seq` (created in Alembic revision `e5c93f28d0b2`).
2. On project create, the service calls `SELECT nextval('project_code_seq')`.
3. The application formats: `{PROJECT_CODE_PREFIX}-{value:0{PAD}d}`.

Defaults:

| Setting | Default | Purpose |
|---------|---------|---------|
| `PROJECT_CODE_PREFIX` | `CRX` | Configurable brand/prefix |
| `PROJECT_CODE_PAD_WIDTH` | `4` | Zero-pad width |

Example: nextval `7` → `CRX-0007`.

## Why not `MAX(project_code)`?

`SELECT MAX(...)` + insert is not safe under concurrency: two sessions can read the same
max and collide. Sequences (`nextval`) are atomic and concurrency-safe.

## Stability

- `project_code` is unique and indexed.
- Codes are assigned once at creation and never rewritten on update/archive.
- Physical deletion of projects is avoided so codes remain valid references for future
  content modules.

## Configuration

Set via environment / `.env`:

```env
PROJECT_CODE_PREFIX=CRX
PROJECT_CODE_PAD_WIDTH=4
```

Changing the prefix affects **new** codes only. Existing codes remain as stored.
