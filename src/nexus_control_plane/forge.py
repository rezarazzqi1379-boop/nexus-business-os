from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class ForgeStage(str, Enum):
    OBSERVE = "observe"
    REVERSE_ENGINEER = "reverse_engineer"
    RECONSTRUCT = "reconstruct"
    BENCHMARK = "benchmark"
    BREAK = "break"
    DIAGNOSE = "diagnose"
    IMPROVE = "improve"
    INTEGRATE = "integrate"
    SANDBOX = "sandbox"
    PROMOTE = "promote"
    EXECUTE = "execute"
    MEASURE = "measure"
    LEARN = "learn"
    EVOLVE = "evolve"


_STAGE_ORDER: tuple[ForgeStage, ...] = tuple(ForgeStage)


class TargetKind(str, Enum):
    AGENT = "agent"
    WORKFLOW = "workflow"
    PROJECT = "project"
    BUSINESS = "business"
    PRODUCT = "product"
    TOOL = "tool"
    SYSTEM = "system"


class PromotionDecision(str, Enum):
    REJECT = "reject"
    EXPERIMENT = "experiment"
    PROMOTABLE = "promotable"


class FailureDisposition(str, Enum):
    CONTINUE_ISOLATED = "continue_isolated"
    CONTAIN_AFFECTED_ACTION = "contain_affected_action"


@dataclass(frozen=True)
class ReverseEngineeringSnapshot:
    snapshot_id: str
    target_id: str
    target_kind: TargetKind
    source_refs: tuple[str, ...]
    observed_mechanisms: tuple[str, ...]
    unknowns: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (self.snapshot_id, self.target_id)
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("snapshot_id and target_id are required")
        if not isinstance(self.target_kind, TargetKind):
            raise ValueError("target_kind must be TargetKind")
        if not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise ValueError("reverse engineering requires retrievable source_refs")
        if not self.observed_mechanisms or any(
            not isinstance(item, str) or not item.strip() for item in self.observed_mechanisms
        ):
            raise ValueError("at least one observed mechanism is required")
        for field_name, values in (("unknowns", self.unknowns), ("constraints", self.constraints)):
            if any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"{field_name} must contain non-empty strings")


@dataclass(frozen=True)
class Reconstruction:
    reconstruction_id: str
    source_snapshot_id: str
    reproduced_mechanisms: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.reconstruction_id.strip() or not self.source_snapshot_id.strip():
            raise ValueError("reconstruction_id and source_snapshot_id are required")
        if not self.reproduced_mechanisms:
            raise ValueError("reconstruction must reproduce at least one mechanism")
        if not self.evidence_refs:
            raise ValueError("reconstruction requires evidence")


@dataclass(frozen=True)
class MetricPair:
    baseline: float
    candidate: float
    higher_is_better: bool = True

    def __post_init__(self) -> None:
        for value in (self.baseline, self.candidate):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise ValueError("metric values must be finite numbers")

    @property
    def normalized_gain(self) -> float:
        raw = self.candidate - self.baseline
        return raw if self.higher_is_better else -raw


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    reconstruction_id: str
    metrics: Mapping[str, MetricPair]
    evidence_refs: tuple[str, ...]
    safety_regressions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.benchmark_id.strip() or not self.reconstruction_id.strip():
            raise ValueError("benchmark_id and reconstruction_id are required")
        if not self.metrics:
            raise ValueError("benchmark requires at least one metric")
        if any(not isinstance(name, str) or not name.strip() for name in self.metrics):
            raise ValueError("metric names must be non-empty strings")
        if any(not isinstance(pair, MetricPair) for pair in self.metrics.values()):
            raise ValueError("metrics must contain MetricPair values")
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("benchmark requires retrievable evidence")
        if any(not isinstance(item, str) or not item.strip() for item in self.safety_regressions):
            raise ValueError("safety regressions must be non-empty strings")

    @property
    def minimum_gain(self) -> float:
        return min(pair.normalized_gain for pair in self.metrics.values())


@dataclass(frozen=True)
class PromotionGateResult:
    decision: PromotionDecision
    reason: str
    requires_human_approval: bool


def next_stage(current: ForgeStage) -> ForgeStage:
    if not isinstance(current, ForgeStage):
        raise ValueError("current must be ForgeStage")
    index = _STAGE_ORDER.index(current)
    if current is ForgeStage.EVOLVE:
        return ForgeStage.OBSERVE
    return _STAGE_ORDER[index + 1]


def validate_transition(current: ForgeStage, requested: ForgeStage) -> None:
    if requested is not next_stage(current):
        raise ValueError(f"invalid Forge transition: {current.value} -> {requested.value}")


def evaluate_promotion(result: BenchmarkResult, *, minimum_gain: float = 0.01) -> PromotionGateResult:
    if not isinstance(minimum_gain, (int, float)) or isinstance(minimum_gain, bool):
        raise ValueError("minimum_gain must be numeric")
    minimum_gain = float(minimum_gain)
    if not math.isfinite(minimum_gain) or minimum_gain < 0:
        raise ValueError("minimum_gain must be finite and non-negative")
    if result.safety_regressions:
        return PromotionGateResult(
            PromotionDecision.REJECT,
            "safety regression detected",
            False,
        )
    if result.minimum_gain < minimum_gain:
        return PromotionGateResult(
            PromotionDecision.EXPERIMENT,
            "candidate has not cleared every required benchmark threshold",
            False,
        )
    return PromotionGateResult(
        PromotionDecision.PROMOTABLE,
        "candidate cleared all benchmark thresholds without recorded safety regression",
        True,
    )


def classify_failure(*, isolated: bool, consequential_risk: bool) -> FailureDisposition:
    """Local failures do not halt unrelated safe work; risky actions are contained."""
    if not isinstance(isolated, bool) or not isinstance(consequential_risk, bool):
        raise ValueError("failure flags must be boolean")
    if consequential_risk or not isolated:
        return FailureDisposition.CONTAIN_AFFECTED_ACTION
    return FailureDisposition.CONTINUE_ISOLATED


def content_write_needed(current_content: str, proposed_content: str) -> bool:
    """Block byte-identical/no-op content writes before they create duplicate history."""
    if not isinstance(current_content, str) or not isinstance(proposed_content, str):
        raise ValueError("content values must be strings")
    return current_content != proposed_content


def build_pr19_evolution_payload(
    *,
    proposal_id: str,
    component: str,
    hypothesis: str,
    change_summary: str,
    source_observations: tuple[str, ...],
    expected_metric: str,
    max_regression: float = 0.0,
) -> dict[str, object]:
    """Emit the existing PR #19 EvolutionProposal contract without duplicating its evaluator."""
    required = (proposal_id, component, hypothesis, change_summary, expected_metric)
    if any(not isinstance(value, str) or not value.strip() for value in required):
        raise ValueError("proposal fields must be non-empty strings")
    if not source_observations or any(not isinstance(ref, str) or not ref.strip() for ref in source_observations):
        raise ValueError("source_observations are required")
    if not isinstance(max_regression, (int, float)) or isinstance(max_regression, bool):
        raise ValueError("max_regression must be numeric")
    max_regression = float(max_regression)
    if not math.isfinite(max_regression) or max_regression < 0:
        raise ValueError("max_regression must be finite and non-negative")
    return {
        "proposal_id": proposal_id,
        "component": component,
        "hypothesis": hypothesis,
        "change_summary": change_summary,
        "source_observations": source_observations,
        "expected_metric": expected_metric,
        "max_regression": max_regression,
    }
