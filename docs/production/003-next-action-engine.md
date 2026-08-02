# Next Action Engine

Every classified production unit gets a **backend-resolved** next action via `resolve_next_action`. The UI should render `code`, `label`, `href`, `reason`, and `blocked` — not invent parallel CTAs from stage alone.

## Shape

```json
{
  "code": "run_quality_review",
  "label": "Run Quality Review",
  "href": "/projects/{project_id}/scripts/{script_id}",
  "reason": "Master Script is ready for AI quality review.",
  "blocked": false
}
```

## Key codes

| Stage / condition | Code |
|-------------------|------|
| `idea` | `create_knowledge_pack` |
| `research` (pack exists) | `open_knowledge_pack` |
| `research` (no pack) | `create_knowledge_pack` |
| `discovery_brief` (with script) | `generate_discovery_brief` |
| `discovery_brief` (no script) | `create_script` |
| `story_spine` | `generate_story_spine` |
| `master_script` | `generate_master_script` |
| `quality_review` | `run_quality_review` |
| `needs_revision` (with generation) | `fix_quality_issues` |
| `ready_for_version` | `create_version` |
| `version_created` | `submit_human_review` |
| `pending_human_review` | `review_approval` / `open_pending_review` |
| `approved` | `view_approved_version` |
| Provider blocker | `configure_ai_provider` |
| Failed AI job | `retry_ai_job` |
| Other blocked | `resolve_blocker` |
| `archived` | `view_approved_version` (`blocked: true`) |

## Design rules

- Actions deep-link into existing surfaces (script workspace, reviews, AI settings). They do not trigger generation themselves.
- No batch “advance all” or auto-generation from Production Mode.
- Provider configuration blockers override stage-specific actions so editors fix credentials before retrying AI paths.

## Related

- [002-production-stage-classification.md](002-production-stage-classification.md)
- Frontend CTAs: [../frontend/015-production-mode-ui.md](../frontend/015-production-mode-ui.md)
