# Factual Risk Review

Quality Review surfaces factual risks for **human verification**. The model does not verify claims against external sources and must not invent certainty.

## Model contract

Each `factual_risks[]` item:

| Field | Notes |
|-------|--------|
| `claim` | Statement in or implied by the narration |
| `risk_level` | `high` \| `medium` \| `low` |
| `reason` | Why verification is needed |
| `verification_needed` | Always forced to `true` on parse/enrich |
| `related_source_note` | Optional pointer into Knowledge Pack sources |

System prompt: never claim external fact verification; every factual risk requires human verification.

## Policy impact

- Any risk with `risk_level=high` → `recommended_next_action = revise`
- `medium` or `high` risks block `ready_for_version` even at high scores
- Low risks still appear for editor attention but do not alone force revise

Priority issues with category `fact` and severity `critical` similarly force revise.

## Human responsibility

Editors must:

1. Check claims against Knowledge Pack sources and primary references  
2. Soften or remove unsupported certainty before Content Version / approval  
3. Treat AI scores and rewrites as drafts — not publication clearance  

AI quality review is **advisory**. Completing a review does not mark the script approved, create a Content Version, or change workflow status.

## Related

- [017-script-quality-review.md](017-script-quality-review.md)
- [018-quality-scoring.md](018-quality-scoring.md)
- [008-knowledge-pack-generation.md](008-knowledge-pack-generation.md) (sources remain unverified until humans check)
