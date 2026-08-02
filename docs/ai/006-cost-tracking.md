# Cost Tracking

Foundation stores pricing metadata and a cost estimator. No live billing.

## Model metadata

`ai_models` columns:

- `pricing_input_per_1k`
- `pricing_output_per_1k`

## Estimator

`app/ai/cost.py` → `estimate_cost_usd(tokens_input, tokens_output, pricing_*)`

Used when generations are persisted in a later sprint. `ai_generations.cost_usd` stores the estimate.

## Settings

Default temperature and max tokens affect future cost envelopes but do not bill anything in v0.16.0.
