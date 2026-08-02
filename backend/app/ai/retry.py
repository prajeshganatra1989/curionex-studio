"""Retry policy for AI jobs (foundation — used by future workers)."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.constants import MAX_JOB_RETRIES


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    next_retry_count: int
    reason: str


def decide_retry(
    *, current_retries: int, error_message: str | None = None
) -> RetryDecision:
    """Return whether a failed job should be re-queued.

    Foundation sprint does not auto-retry. This policy is shared so future
    workers apply consistent limits without scattering magic numbers.
    """
    next_count = current_retries + 1
    if next_count > MAX_JOB_RETRIES:
        return RetryDecision(
            should_retry=False,
            next_retry_count=current_retries,
            reason="max_retries_exceeded",
        )
    # Transient-looking messages may be retried by a future worker.
    transient_markers = ("timeout", "rate limit", "temporarily", "503", "429")
    message = (error_message or "").lower()
    if any(marker in message for marker in transient_markers):
        return RetryDecision(
            should_retry=True,
            next_retry_count=next_count,
            reason="transient_error",
        )
    return RetryDecision(
        should_retry=False,
        next_retry_count=current_retries,
        reason="non_retryable",
    )
