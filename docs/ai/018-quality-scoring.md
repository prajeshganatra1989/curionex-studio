# Quality Scoring

Server-side scoring policy for Script Quality Review. The model proposes per-dimension scores; the backend recalculates the overall score and recommendation.

## Dimensions and weights

Fourteen dimensions; weights total **100**:

| Dimension | Weight |
|-----------|--------|
| hook | 10 |
| curiosity | 8 |
| retention | 12 |
| clarity | 10 |
| structure | 8 |
| factual_safety | 12 |
| viewer_promise | 8 |
| payoff | 8 |
| pacing | 7 |
| spoken_naturalness | 6 |
| conciseness | 4 |
| brand_voice | 3 |
| call_to_action | 2 |
| duration_fit | 2 |

Defined in `app.ai.script_quality_review.DIMENSION_WEIGHTS`.

## Weighted overall score

```
calculated = round(Σ dimension.score × (weight / 100))
```

Enrichment stores:

| Field | Source |
|-------|--------|
| `model_overall_score` | Model `overall_score` as returned |
| `overall_score` / `calculated_overall_score` | Server weighted score (displayed) |
| `score_weights` | Copy of `DIMENSION_WEIGHTS` |

If model and calculated scores differ, a warning is added noting the server-calculated display score.

## Quality bands

| Score | Band |
|------:|------|
| ≥ 90 | `excellent` |
| ≥ 80 | `strong` |
| ≥ 70 | `needs_refinement` |
| ≥ 60 | `weak` |
| &lt; 60 | `major_revision_required` |

Labels are human-readable via `quality_band_label`.

## Recommended next action

Computed from **calculated** score + factual risks + priority issues:

1. Any **high** factual risk **or** **critical** priority issue → `revise`
2. Score &lt; 80 → `revise`
3. Score ≥ 90 **and** no high/medium factual risks **and** no critical/high issues → `ready_for_version`
4. Otherwise → `human_review`

There is **no** auto-approve outcome. `ai_approval` is always `false`.

## Deterministic pacing metrics

Word count and duration are computed from Master Script text (same `word_count` as draft pipeline), not trusted from the model:

- `estimated_duration_seconds` = round((words / WPM) × 60), minimum 1  
- Pacing status vs target duration ±10% word-count tolerance  
- Stored under `deterministic_metrics` and merged into `pacing_analysis` (AI may still supply slow/rushed section notes)

## Schema validation

Invalid dimension scores (outside 0–100), missing dimensions, unknown issue categories, or other schema violations fail the job (`StructuredOutputError`) — no generation row.

## Related

- [017-script-quality-review.md](017-script-quality-review.md)
- [019-factual-risk-review.md](019-factual-risk-review.md)
