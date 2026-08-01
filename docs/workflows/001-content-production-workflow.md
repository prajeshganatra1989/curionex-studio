# Content Production Workflow

M2I connects existing Curionex Studio domains into one production lifecycle.

## Lifecycle chain

```
Project
  → Knowledge Pack
    → Script Workspace (ScriptDocuments)
      → ContentVersion (immutable snapshot)
        → Approval (decision on exact version)
          → Workflow orchestration (stage/status only)
```

## Responsibilities

| Domain | Responsibility |
|--------|----------------|
| Project | Project metadata and membership |
| Knowledge Pack | Research / context |
| Script + ScriptDocument | Editable workspace content |
| ContentVersion | Immutable snapshot (M2G) |
| Approval | Review decision for an exact ContentVersion (M2G) |
| ContentWorkflow | Lifecycle / state coordination only |

## What Workflow is not

Workflow does **not** store document content, duplicate versioning, or replace Approvals.

M2G remains the canonical versioning and approval system.

## Future automation (not in M2I)

Knowledge Pack → AI / automation → Discovery Brief → Story Spine → Master Script → ContentVersion → Approval → voice / video / publishing.

M2I only orchestrates the human-editable path through workspace, versioning, review, and completion.
