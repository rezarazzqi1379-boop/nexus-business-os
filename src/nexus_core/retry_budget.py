from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FailureKind = Literal["timeout", "rate_limit", "transient", "auth", "permission", "validation", "unknown"]
CircuitState = Literal["closed", "open", "half_open"]
_ALLOWED_FAILURES = {"timeout", "rate_limit", "transient", "auth", "permission", "validation", "unknown"}


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


def _valid_policy(policy: object) -> bool:
    if not isinstance(policy, RetryPolicy):
        return False
    values = (
        policy.max_attempts,
        policy.base_delay_ms,
        policy.max_delay_ms,
        policy.jitter_ms,
        policy.open_after_failures,
    )
    if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
        return False
    if policy.max_attempts < 1 or policy.open_after_failures < 1:
        return False
    if policy.base_delay_ms < 0 or policy.max_delay_ms < 0 or policy.jitter_ms < 0:
        return False
    if policy.max_delay_ms < policy.base_delay_ms:
        return False
    return True


def decide_retry(
    *,
    failure: FailureKind,
    attempt: int,
    consecutive_failures: int,
    policy: RetryPolicy = RetryPolicy(),
) -> RetryDecision:
    """Return a bounded retry decision without authorizing replay of an external side effect.

    Callers remain responsible for idempotency/deduplication and Human Gates. Malformed
    runtime values fail closed into a no-retry/open-circuit decision rather than raising.
    """
    if not _valid_policy(policy):
        return RetryDecision(False, 0, "open", "invalid_retry_policy")
    if not isinstance(failure, str) or failure not in _ALLOWED_FAILURES:
        return RetryDecision(False, 0, "open", "unsupported_failure")
    if (
        not isinstance(attempt, int)
        or isinstance(attempt, bool)
        or not isinstance(consecutive_failures, int)
        or isinstance(consecutive_failures, bool)
        or attempt < 1
        or consecutive_failures < 1
    ):
        return RetryDecision(False, 0, "open", "invalid_failure_count")
    if failure in {"auth", "permission", "validation"}:
        return RetryDecision(False, 0, "open", f"non_retryable_{failure}")
    if consecutive_failures >= policy.open_after_failures:
        return RetryDecision(False, 0, "open", "failure_threshold_reached")
    if attempt >= policy.max_attempts:
        return RetryDecision(False, 0, "open", "retry_budget_exhausted")
    exponential = policy.base_delay_ms * (2 ** (attempt - 1))
    delay = min(policy.max_delay_ms, exponential) + min(policy.jitter_ms, attempt * 17)
    return RetryDecision(True, delay, "closed", "bounded_backoff")


def half_open_probe(*, probe_succeeded: bool) -> RetryDecision:
    if not isinstance(probe_succeeded, bool):
        return RetryDecision(False, 0, "open", "invalid_probe_result")
    if probe_succeeded is True:
        return RetryDecision(False, 0, "closed", "probe_recovered")
    return RetryDecision(False, 0, "open", "probe_failed")
