# Script Document Types (M2H)

Centralized in `app/scripts/catalog.py`.

| Type | Position | Purpose |
|------|----------|---------|
| `discovery_brief` | 1 | Structured discovery brief for the workspace |
| `story_spine` | 2 | Narrative spine / story structure |
| `master_script` | 3 | Full master script draft |

Unique per script: `(script_id, document_type)`.

Content is plain text and editable in M2H. Immutability arrives when content is
snapshotted into `ContentVersion` (M2G) in a later workflow step.
