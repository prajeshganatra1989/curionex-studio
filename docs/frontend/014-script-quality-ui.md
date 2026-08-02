# Frontend — Script Quality UI

## Placement

Script workspace Master Script surface: **Run Quality Review** alongside existing AI draft actions. Reviews are advisory — copy must state that AI does not approve content and factual claims need human verification.

## Run review

Dialog / panel:

- Model (OpenAI; blank = studio default)  
- Language, target duration, WPM  
- Warning when Discovery Brief or Story Spine is empty (review still allowed)  
- Disabled when Master Script is empty  
- `idempotency_key` on submit; poll job until terminal; cancel while queued  

Dirty Save before Generate pattern from script drafting applies: persist Master Script before queueing so fingerprints match.

## Results panel

After completion, show:

- Overall **server** score, quality band, confidence  
- Recommended next action (`revise` / `human_review` / `ready_for_version`) — never an “Approved by AI” badge  
- Dimension breakdown (scores + short assessments)  
- Priority issues list (severity, category, problem, suggested rewrite)  
- Factual risks with **HUMAN CHECK REQUIRED** emphasis  
- Deterministic word count / duration vs target  
- Context / score-mismatch warnings  
- Stale-input banner when Master (or fingerprint inputs) changed after the review  

List/history: `GET …/ai-quality-reviews`; open latest via `…/latest`.

## Apply suggestion

Per issue with excerpt + rewrite: **Apply rewrite** → `replace_excerpt`.

- Confirm before mutating Master Script  
- Surface 409 for missing / ambiguous excerpt and stale review  
- On success, refresh Master Script document only; keep other dirty docs  
- Do not auto-create Content Version  

## Permissions

| Action | Permission |
|--------|------------|
| Run review | `ai.generate` |
| View reviews | `ai.view` |
| Apply suggestion | `scripts.update` |

Reviewer-only roles can view results but not generate or apply.

## Copy principles

- AI is advisory; editors remain accountable for facts and publication  
- Never imply auto-approval from high scores or `ready_for_version`  
- Pair factual risks with source / Knowledge Pack links when available  

## Related

- [013-ai-script-drafting.md](013-ai-script-drafting.md)
- Backend: [../ai/017-script-quality-review.md](../ai/017-script-quality-review.md), [../ai/020-quality-suggestions.md](../ai/020-quality-suggestions.md)
