# Production Stage Classification

Stages are **derived** at read time by `classify_production_stage(ClassificationInput)` in `app/production/stages.py`. Nothing persists a production stage on Script or Project.

## Stage catalog

| Stage | Typical meaning |
|-------|-----------------|
| `idea` | Project with no Knowledge Pack and no Script |
| `research` | Project-only unit with a Knowledge Pack (complete or not) |
| `discovery_brief` | Script exists; Discovery Brief empty |
| `story_spine` | Discovery Brief present; Story Spine empty |
| `master_script` | Story Spine present; Master Script empty |
| `quality_review` | Master Script present; no usable quality generation yet |
| `needs_revision` | Quality gate failed, stale, critical issues, or rejected version |
| `ready_for_version` | Quality recommends versioning; workspace ready for ContentVersion |
| `version_created` | Draft ContentVersion exists; not yet in human review |
| `pending_human_review` | Pending Approval (or `in_review` without pending edge case) |
| `approved` | Workflow completed, or approved version + approved script |
| `blocked` | Provider misconfigured, failed AI job, or workflow blocked |
| `archived` | Script or project status is archived |

## Precedence (first match wins)

1. `archived`
2. `approved`
3. `blocked`
4. `pending_human_review`
5. `version_created` (and rejected → `needs_revision`)
6. `needs_revision` (quality / stale / score gates)
7. `ready_for_version`
8. `quality_review`
9. Document ladder: `master_script` → `story_spine` → `discovery_brief`
10. Project-only: `research` / `idea`

Archived beats approved; approved beats blocked; blocked beats pending review. This keeps terminal and blocker states visible even when lower-priority signals also exist.

## Inputs (not content bodies)

`ClassificationInput` carries presence flags, workflow/approval/job snapshots, quality summaries, and version fingerprint match — not document text. Queue JSON exposes document **statuses** (`complete` / `incomplete` / `missing`) only.

## Queue priority

`STAGE_PRIORITY` orders the queue (lower = higher priority): blocked and pending review first; archived last. Default sort is priority then `updated_at` descending.

## Related

- [001-production-mode.md](001-production-mode.md)
- [003-next-action-engine.md](003-next-action-engine.md)
- Workflow states: [../workflows/002-workflow-states.md](../workflows/002-workflow-states.md)
