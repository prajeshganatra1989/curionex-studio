# Workflow States

## Stages (where the work is)

| Stage | Meaning |
|-------|---------|
| `workspace` | ScriptDocuments are being prepared/edited |
| `versioning` | A ContentVersion snapshot is prepared / active for review submission |
| `review` | A ContentVersion has been submitted for approval |
| `completed` | The workflow has an approved version |

## Statuses (operational condition)

| Status | Meaning |
|--------|---------|
| `active` | Workflow is progressing |
| `blocked` | Reserved for future operational holds |
| `completed` | Workflow finished successfully |
| `archived` | Soft-closed; historical data retained |

Stage and status are independent concepts. Do not collapse them.

## Allowed stage transitions

```
workspace  → versioning
versioning → review
review     → completed   (only when active version is approved)
review     → workspace   (only when active version is rejected)
```

Archive is a **status** change (not a stage):

- Allowed from stages: `workspace`, `versioning`, `review`
- Sets `status = archived`
- Does not delete Script, documents, versions, or approvals

## Initial state

When a Script is created, its ContentWorkflow is created in the same transaction:

- `current_stage = workspace`
- `status = active`
