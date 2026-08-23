from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceMetrics:
    accepted_decisions: int
    stale_memory_rejections: int
    source_authority_violations: int
    cross_project_contamination: int
    contradictions_detected: int
    recoverable_failures: int
    recovered_failures: int
    human_overrides: int
    duplicate_actions: int
    tool_calls: int
    context_units: int

    @property
    def recovery_rate(self) -> float:
        return 1.0 if self.recoverable_failures == 0 else self.recovered_failures / self.recoverable_failures

    @property
    def tool_calls_per_accepted_decision(self) -> float:
        return 0.0 if self.accepted_decisions == 0 else self.tool_calls / self.accepted_decisions

    @property
    def context_units_per_accepted_decision(self) -> float:
        return 0.0 if self.accepted_decisions == 0 else self.context_units / self.accepted_decisions


@dataclass(frozen=True)
class BenchmarkDelta:
    recovery_rate_delta: float
    stale_memory_rejection_delta: int
    source_authority_violation_delta: int
    cross_project_contamination_delta: int
    duplicate_action_delta: int
    tool_calls_per_decision_delta: float
    context_units_per_decision_delta: float
    promotable: bool
    reasons: tuple[str, ...]


def compare_intelligence(baseline: IntelligenceMetrics, candidate: IntelligenceMetrics) -> BenchmarkDelta:
    """Compare deterministic replay metrics.

    This is a contract/replay benchmark, not production ROI. Promotion requires zero
    authority/cross-project regressions, no duplicate-action regression, non-worse
    recovery, and lower-or-equal tool/context overhead per accepted decision.
    """
    if not isinstance(baseline, IntelligenceMetrics) or not isinstance(candidate, IntelligenceMetrics):
        raise TypeError("baseline and candidate must be IntelligenceMetrics")

    reasons: list[str] = []
    if candidate.source_authority_violations > baseline.source_authority_violations:
        reasons.append("source-authority violations regressed")
    if candidate.cross_project_contamination > baseline.cross_project_contamination:
        reasons.append("cross-project contamination regressed")
    if candidate.duplicate_actions > baseline.duplicate_actions:
        reasons.append("duplicate actions regressed")
    if candidate.recovery_rate < baseline.recovery_rate:
        reasons.append("recovery rate regressed")
    if candidate.tool_calls_per_accepted_decision > baseline.tool_calls_per_accepted_decision:
        reasons.append("tool calls per accepted decision increased")
    if candidate.context_units_per_accepted_decision > baseline.context_units_per_accepted_decision:
        reasons.append("context overhead per accepted decision increased")

    positive = (
        candidate.stale_memory_rejections > baseline.stale_memory_rejections
        or candidate.recovery_rate > baseline.recovery_rate
        or candidate.duplicate_actions < baseline.duplicate_actions
        or candidate.tool_calls_per_accepted_decision < baseline.tool_calls_per_accepted_decision
        or candidate.context_units_per_accepted_decision < baseline.context_units_per_accepted_decision
        or candidate.source_authority_violations < baseline.source_authority_violations
        or candidate.cross_project_contamination < baseline.cross_project_contamination
    )
    if not positive:
        reasons.append("no measurable replay improvement")

    promotable = not reasons and positive
    return BenchmarkDelta(
        recovery_rate_delta=candidate.recovery_rate - baseline.recovery_rate,
        stale_memory_rejection_delta=candidate.stale_memory_rejections - baseline.stale_memory_rejections,
        source_authority_violation_delta=candidate.source_authority_violations - baseline.source_authority_violations,
        cross_project_contamination_delta=candidate.cross_project_contamination - baseline.cross_project_contamination,
        duplicate_action_delta=candidate.duplicate_actions - baseline.duplicate_actions,
        tool_calls_per_decision_delta=(
            candidate.tool_calls_per_accepted_decision - baseline.tool_calls_per_accepted_decision
        ),
        context_units_per_decision_delta=(
            candidate.context_units_per_accepted_decision - baseline.context_units_per_accepted_decision
        ),
        promotable=promotable,
        reasons=tuple(reasons),
    )
