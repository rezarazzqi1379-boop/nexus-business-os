from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FailureKind = Literal["timeout", "rate_limit", "transient", "auth", "permission", "validation", "unknown"]
CircuitState = Literal["closed", "open", "half_open"]


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_ms: int = 250
    max_delay_ms: int = 4000
    jitter_ms: int = 100
    open_after_failures: int = 3


@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    delay_ms: int
    circuit: CircuitState
    reason: str


def decide_retry(
    *,
    failure: FailureKind,
    attempt: int,
    consecutive_failures: int,
    policy: RetryPolicy = RetryPolicy(),
) -> RetryDecision:
    if min(policy.max_attempts, policy.base_delay_ms, policy.max_delay_ms, policy.jitter_ms, policy.open_after_failures) < 0:
        raise ValueError("invalid_retry_policy")
    if attempt < 1 or consecutive_failures < 1:
        raise ValueError("invalid_failure_count")
    if failure in {"auth", "permission", "validation"}:
        return RetryDecision(False, 0, "open", f"non_retryable_{failure}")
    if consecutive_failures >= policy.open_after_failures:
        return RetryDecision(False, 0, "open", "failure_threshold_reached")
    if attempt >= policy.max_attempts:
        return RetryDecision(False, 0, "open", "retry_budget_exhausted")
    if failure not in {"timeout", "rate_limit", "transient", "unknown"}:
        return RetryDecision(False, 0, "open", "unsupported_failure")
    exponential = policy.base_delay_ms * (2 ** (attempt - 1))
    delay = min(policy.max_delay_ms, exponential) + min(policy.jitter_ms, attempt * 17)
    return RetryDecision(True, delay, "closed", "bounded_backoff")


def half_open_probe(*, probe_succeeded: bool) -> RetryDecision:
    if probe_succeeded:
        return RetryDecision(False, 0, "closed", "probe_recovered")
    return RetryDecision(False, 0, "open", "probe_failed")
