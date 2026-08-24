from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostForecast:
    monthly_runs: int
    monthly_input_tokens: int
    monthly_output_tokens: int
    model_cost_usd: float


def forecast_cost(
    *, runs_per_day: int, days: int, input_tokens_per_run: int, output_tokens_per_run: int,
    input_usd_per_million: float, output_usd_per_million: float,
) -> CostForecast:
    values = (runs_per_day, days, input_tokens_per_run, output_tokens_per_run)
    if any(value < 0 for value in values) or input_usd_per_million < 0 or output_usd_per_million < 0:
        raise ValueError("invalid_cost_input")
    runs = runs_per_day * days
    input_tokens, output_tokens = runs * input_tokens_per_run, runs * output_tokens_per_run
    cost = input_tokens / 1_000_000 * input_usd_per_million + output_tokens / 1_000_000 * output_usd_per_million
    return CostForecast(runs, input_tokens, output_tokens, round(cost, 4))

