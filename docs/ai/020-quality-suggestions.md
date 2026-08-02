# Quality Suggestions

Targeted Master Script edits from Quality Review priority issues. Apply is explicit, excerpt-based, and fingerprint-gated.

## Priority issues

Up to **10** issues (`MAX_PRIORITY_ISSUES`), sorted by severity then id:

| Field | Role |
|-------|------|
| `id` | Stable issue key used in apply URL |
| `severity` | `critical` \| `high` \| `medium` \| `low` |
| `category` | hook, fact, retention, clarity, pacing, structure, payoff, language, cta, brand_voice |
| `original_excerpt` | Exact substring expected in current Master Script (max 400 chars) |
| `suggested_rewrite` | Replacement text (max 800 chars); required to apply |
| `problem` / `recommended_change` | Editorial guidance |

Issues without both excerpt and rewrite cannot be applied.

## Apply API

`POST /scripts/{script_id}/ai-quality-reviews/{generation_id}/suggestions/{issue_id}/apply`

Body: `{ "strategy": "replace_excerpt" }` (only strategy in this release).

Requires `scripts.update`.

### Success

1. Review job must be `completed`  
2. Generation must belong to the script  
3. Input fingerprint must still match (not stale)  
4. `original_excerpt` occurs **exactly once** in Master Script  
5. Replace that occurrence with `suggested_rewrite`  
6. Record `issue:{id}` on `applied_sections_json`; audit suggestion applied  

Does **not** create a Content Version. Does not re-run quality review.

### Rejects

| Condition | HTTP | Code / signal |
|-----------|------|----------------|
| Excerpt not in script | 409 | `excerpt_not_found` |
| Excerpt appears more than once | 409 | `excerpt_ambiguous` |
| Master / pack / voice / policy fingerprint changed | 409 | `stale_review` |
| Missing rewrite/excerpt, wrong strategy, incomplete job | 422 | validation |
| Unknown issue / generation | 404 | — |

Stale applies are **rejected** (stricter than script draft apply, which allows apply with `stale_input: true`).

## Audit

`script.quality_suggestion_applied` metadata includes generation/job ids, issue id, category, severity, strategy, scores — **not** full script body, excerpt, or rewrite text.

## Related

- [017-script-quality-review.md](017-script-quality-review.md)
- [015-ai-input-fingerprints.md](015-ai-input-fingerprints.md)
- Frontend: [../frontend/014-script-quality-ui.md](../frontend/014-script-quality-ui.md)
