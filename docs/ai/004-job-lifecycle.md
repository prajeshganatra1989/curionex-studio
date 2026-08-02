# AI Job Lifecycle

Generation requests become jobs. v0.16.0 queues jobs only — no live execution.

## States

| Status | Meaning |
|--------|---------|
| `queued` | Accepted; waiting for a future worker |
| `running` | Reserved for live execution |
| `completed` | Reserved for successful generation |
| `failed` | Reserved for provider/runtime failures |
| `cancelled` | Cancelled while queued or running |

## Create flow (foundation)

1. Resolve prompt active version + model + provider.
2. Validate input variables against the version.
3. Render templates (validation only — output discarded).
4. Insert `ai_jobs` with `status=queued`.
5. Audit `ai.job_queued`.

No `ai_generations` row is written in this sprint.

## Cancel

Queued or running jobs may be cancelled (`ai.generate`). Terminal states reject cancel with HTTP 409.

## Retry policy

`app/ai/retry.py` centralizes max retries (`MAX_JOB_RETRIES`) and transient-error heuristics for future workers. Foundation does not auto-retry.
