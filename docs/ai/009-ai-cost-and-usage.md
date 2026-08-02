# AI Cost and Usage (v0.17.0)

## Token usage

Captured from the OpenAI Responses API `usage` object into:

- `ai_generations.tokens_input`
- `ai_generations.tokens_output`
- `ai_generations.tokens_total`

## Pricing metadata

Stored on `ai_models`:

- `pricing_input_per_1k`
- `pricing_output_per_1k`

Estimator: `app/ai/cost.py` → `estimate_cost_usd`.

## Estimated cost

When usage **and** pricing exist, `cost_usd` is stored. UI must label costs as **estimated**.

If pricing is missing, `cost_usd` stays `null` — services never invent prices.

## Why pricing is not hard-coded in services

Provider prices change. Keeping rates on model rows lets operators update metadata without redeploying pricing logic.
