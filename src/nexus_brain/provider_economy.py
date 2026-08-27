from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


@dataclass(frozen=True)
class ProviderObservation:
    provider_id: str
    observed_at: str
    healthy: bool
    latency_ms: float
    success_rate: float
    eval_score: float
    estimated_cost_usd: float
    sample_count: int

    def validate(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("invalid_provider_id")
        observed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if observed.tzinfo is None:
            raise ValueError("observation_requires_timezone")
        if self.latency_ms < 0 or self.estimated_cost_usd < 0 or self.sample_count < 0:
            raise ValueError("negative_observation_metric")
        if not 0 <= self.success_rate <= 1 or not 0 <= self.eval_score <= 1:
            raise ValueError("observation_metric_out_of_range")


@dataclass(frozen=True)
class EconomyPolicy:
    max_observation_age_seconds: int = 3600
    minimum_success_rate: float = 0.95
    minimum_eval_score: float = 0.75
    minimum_sample_count: int = 3
    max_estimated_cost_usd: float = 0.02
    max_latency_ms: float = 30_000

    def validate(self) -> None:
        if self.max_observation_age_seconds <= 0 or self.minimum_sample_count < 1:
            raise ValueError("invalid_economy_policy")
        if not 0 <= self.minimum_success_rate <= 1 or not 0 <= self.minimum_eval_score <= 1:
            raise ValueError("invalid_economy_policy")
        if self.max_estimated_cost_usd < 0 or self.max_latency_ms <= 0:
            raise ValueError("invalid_economy_policy")


@dataclass(frozen=True)
class EconomyDecision:
    provider_id: str | None
    allowed: bool
    reason: str
    ranked_candidates: tuple[str, ...] = ()
    rejected: tuple[str, ...] = ()


def _age_seconds(observed_at: str, now: datetime) -> float:
    observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    if observed.tzinfo is None:
        raise ValueError("observation_requires_timezone")
    return (now - observed.astimezone(timezone.utc)).total_seconds()


def select_economic_provider(
    observations: Iterable[ProviderObservation],
    *,
    policy: EconomyPolicy,
    permitted_provider_ids: Iterable[str],
    now: datetime | None = None,
) -> EconomyDecision:
    """Rank already-policy-permitted providers from trusted observations only.

    This function never probes providers, reads credentials, performs network calls, or
    changes provider policy approval. It is a shadow-selection layer beneath ResourceRouter.
    """
    policy.validate()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now_requires_timezone")
    current = current.astimezone(timezone.utc)
    permitted = set(permitted_provider_ids)

    seen: set[str] = set()
    ranked: list[tuple[float, str]] = []
    rejected: list[str] = []

    for observation in observations:
        observation.validate()
        if observation.provider_id in seen:
            raise ValueError("duplicate_provider_observation")
        seen.add(observation.provider_id)
        pid = observation.provider_id

        if pid not in permitted:
            rejected.append(f"{pid}:not_policy_permitted")
            continue
        age = _age_seconds(observation.observed_at, current)
        if age < 0:
            rejected.append(f"{pid}:observation_from_future")
            continue
        if age > policy.max_observation_age_seconds:
            rejected.append(f"{pid}:stale_observation")
            continue
        if not observation.healthy:
            rejected.append(f"{pid}:unhealthy")
            continue
        if observation.sample_count < policy.minimum_sample_count:
            rejected.append(f"{pid}:insufficient_samples")
            continue
        if observation.success_rate < policy.minimum_success_rate:
            rejected.append(f"{pid}:success_rate_below_threshold")
            continue
        if observation.eval_score < policy.minimum_eval_score:
            rejected.append(f"{pid}:eval_below_threshold")
            continue
        if observation.estimated_cost_usd > policy.max_estimated_cost_usd:
            rejected.append(f"{pid}:cost_above_budget")
            continue
        if observation.latency_ms > policy.max_latency_ms:
            rejected.append(f"{pid}:latency_above_threshold")
            continue

        # Quality/reliability dominate; lower cost and latency break close ties.
        cost_score = 1.0 if policy.max_estimated_cost_usd == 0 and observation.estimated_cost_usd == 0 else (
            0.0 if policy.max_estimated_cost_usd == 0 else 1 - observation.estimated_cost_usd / policy.max_estimated_cost_usd
        )
        latency_score = max(0.0, 1 - observation.latency_ms / policy.max_latency_ms)
        score = (
            observation.eval_score * 50
            + observation.success_rate * 30
            + cost_score * 12
            + latency_score * 8
        )
        ranked.append((score, pid))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    if not ranked:
        return EconomyDecision(
            provider_id=None,
            allowed=False,
            reason="No policy-permitted provider has fresh evidence meeting quality, reliability, budget and latency gates.",
            rejected=tuple(rejected),
        )

    ordered = tuple(pid for _, pid in ranked)
    return EconomyDecision(
        provider_id=ordered[0],
        allowed=True,
        reason="Selected from policy-permitted providers using fresh observed quality, reliability, cost and latency evidence.",
        ranked_candidates=ordered,
        rejected=tuple(rejected),
    )
