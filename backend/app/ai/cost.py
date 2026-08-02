"""Cost estimation helpers for AI generations (no live billing)."""

from __future__ import annotations


def estimate_cost_usd(
    *,
    tokens_input: int | None,
    tokens_output: int | None,
    pricing_input_per_1k: float | None,
    pricing_output_per_1k: float | None,
) -> float | None:
    if pricing_input_per_1k is None and pricing_output_per_1k is None:
        return None
    total = 0.0
    if tokens_input and pricing_input_per_1k is not None:
        total += (tokens_input / 1000.0) * pricing_input_per_1k
    if tokens_output and pricing_output_per_1k is not None:
        total += (tokens_output / 1000.0) * pricing_output_per_1k
    return round(total, 6)
