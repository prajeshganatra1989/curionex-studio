# Source of Truth

Each domain owns one concern. Workflow is orchestration only.

| Source of truth | Owns |
|-----------------|------|
| **Project** | Project metadata, membership, codes |
| **Knowledge Pack** | Research / context sections |
| **ScriptDocument** | Current editable workspace content |
| **ContentVersion** | Immutable content snapshot |
| **Approval** | Review decision for an exact ContentVersion |
| **ContentWorkflow** | Lifecycle stage/status coordination |

## Version concepts (do not collapse)

| Concept | Meaning |
|---------|---------|
| **Latest version** | Highest `version_number` for the project |
| **Active version** | `ContentWorkflow.active_content_version_id` — version currently processed by the workflow |
| **Approved version** | Latest ContentVersion with status `approved` |

Active is not latest. Active is not approved. Approved is not necessarily active.

## Rules

- Do not duplicate ScriptDocument content inside Workflow
- Do not create parallel versioning or approval tables for workflows
- Do not mutate rejected ContentVersions
- Do not bypass M2G Approval for completion
