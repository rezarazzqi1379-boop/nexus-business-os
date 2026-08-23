from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class GenerationDecision(str, Enum):
    CONTINUE = "continue"
    SELF_STOP_AUDIT = "self_stop_audit"
    ROLLBACK_RESTART = "rollback_restart"
    PROMOTE_RESTART = "promote_restart"
    PLATEAU_RESEARCH_RESTART = "plateau_research_restart"


class StopReason(str, Enum):
    NONE = "none"
    ACTION_BUDGET = "action_budget"
    COST_BUDGET = "cost_budget"
    TIME_BUDGET = "time_budget"
    RETRY_BUDGET = "retry_budget"
    SAFETY_REGRESSION = "safety_regression"
    FAILURE_RATE = "failure_rate"
    MARGINAL_GAIN = "marginal_gain"
    ARCHITECTURE_SPRAWL = "architecture_sprawl"
    CONTRADICTION_LOAD = "contradiction_load"


@dataclass(frozen=True)
class EvolutionBudget:
    max_actions: int
    max_cost_units: float
    max_runtime_seconds: float
    max_retries: int

    def __post_init__(self) -> None:
        if not isinstance(self.max_actions, int) or isinstance(self.max_actions, bool) or self.max_actions <= 0:
            raise ValueError("max_actions must be a positive integer")
        if not isinstance(self.max_retries, int) or isinstance(self.max_retries, bool) or self.max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        for name, value in (("max_cost_units", self.max_cost_units), ("max_runtime_seconds", self.max_runtime_seconds)):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")


@dataclass(frozen=True)
class GenerationTelemetry:
    generation_id: str
    actions_used: int
    cost_units_used: float
    runtime_seconds: float
    retries_used: int
    failures: int
    evaluations: int
    minimum_gain: float
    safety_regressions: int = 0
    architecture_sprawl_events: int = 0
    contradiction_events: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.generation_id, str) or not self.generation_id.strip() or self.generation_id != self.generation_id.strip():
            raise ValueError("generation_id must be a non-empty normalized string")
        for name, value in (("actions_used", self.actions_used), ("retries_used", self.retries_used), ("failures", self.failures), ("evaluations", self.evaluations), ("safety_regressions", self.safety_regressions), ("architecture_sprawl_events", self.architecture_sprawl_events), ("contradiction_events", self.contradiction_events)):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name, value in (("cost_units_used", self.cost_units_used), ("runtime_seconds", self.runtime_seconds), ("minimum_gain", self.minimum_gain)):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite numeric")
        if self.cost_units_used < 0 or self.runtime_seconds < 0:
            raise ValueError("usage metrics cannot be negative")

    @property
    def failure_rate(self) -> float:
        return 0.0 if self.evaluations == 0 else self.failures / self.evaluations


@dataclass(frozen=True)
class GenerationAudit:
    telemetry: GenerationTelemetry
    stop_reason: StopReason
    decision: GenerationDecision
    requires_human_approval: bool
    rollback_required: bool
    research_refresh_required: bool


def evaluate_generation(
    telemetry: GenerationTelemetry,
    budget: EvolutionBudget,
    *,
    maximum_failure_rate: float = 0.20,
    minimum_meaningful_gain: float = 0.01,
    maximum_sprawl_events: int = 0,
    maximum_contradiction_events: int = 0,
) -> GenerationAudit:
    """Evaluate one bounded generation of an open-ended recursive evolution loop.

    The loop may continue across arbitrarily many generations, but each generation must
    stop for audit when a budget, safety, quality, contradiction or marginal-gain
    boundary is reached. This function never authorizes external execution.
    """

    if not isinstance(telemetry, GenerationTelemetry) or not isinstance(budget, EvolutionBudget):
        raise ValueError("telemetry and budget must use recursive evolution types")
    for name, value in (("maximum_failure_rate", maximum_failure_rate), ("minimum_meaningful_gain", minimum_meaningful_gain)):
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value < 0:
            raise ValueError(f"{name} must be finite and non-negative")
    for name, value in (("maximum_sprawl_events", maximum_sprawl_events), ("maximum_contradiction_events", maximum_contradiction_events)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    # Highest-severity conditions are evaluated first and always contain the generation.
    if telemetry.safety_regressions > 0:
        return GenerationAudit(telemetry, StopReason.SAFETY_REGRESSION, GenerationDecision.ROLLBACK_RESTART, False, True, False)
    if telemetry.architecture_sprawl_events > maximum_sprawl_events:
        return GenerationAudit(telemetry, StopReason.ARCHITECTURE_SPRAWL, GenerationDecision.SELF_STOP_AUDIT, False, False, False)
    if telemetry.contradiction_events > maximum_contradiction_events:
        return GenerationAudit(telemetry, StopReason.CONTRADICTION_LOAD, GenerationDecision.SELF_STOP_AUDIT, False, False, True)
    if telemetry.evaluations > 0 and telemetry.failure_rate > maximum_failure_rate:
        return GenerationAudit(telemetry, StopReason.FAILURE_RATE, GenerationDecision.SELF_STOP_AUDIT, False, False, False)

    if telemetry.actions_used >= budget.max_actions:
        return GenerationAudit(telemetry, StopReason.ACTION_BUDGET, GenerationDecision.SELF_STOP_AUDIT, False, False, False)
    if telemetry.cost_units_used >= budget.max_cost_units:
        return GenerationAudit(telemetry, StopReason.COST_BUDGET, GenerationDecision.SELF_STOP_AUDIT, False, False, False)
    if telemetry.runtime_seconds >= budget.max_runtime_seconds:
        return GenerationAudit(telemetry, StopReason.TIME_BUDGET, GenerationDecision.SELF_STOP_AUDIT, False, False, False)
    if telemetry.retries_used >= budget.max_retries and budget.max_retries > 0:
        return GenerationAudit(telemetry, StopReason.RETRY_BUDGET, GenerationDecision.SELF_STOP_AUDIT, False, False, False)

    if telemetry.evaluations > 0 and telemetry.minimum_gain < minimum_meaningful_gain:
        return GenerationAudit(telemetry, StopReason.MARGINAL_GAIN, GenerationDecision.PLATEAU_RESEARCH_RESTART, False, False, True)

    return GenerationAudit(telemetry, StopReason.NONE, GenerationDecision.CONTINUE, False, False, False)


def finalize_stopped_generation(
    audit: GenerationAudit,
    *,
    independent_audit_passed: bool,
    candidate_beats_baseline: bool,
) -> GenerationAudit:
    """Convert a stopped generation into the next-generation instruction.

    Promotion still requires a human gate; rollback and research restart do not.
    """
    if not isinstance(audit, GenerationAudit):
        raise ValueError("audit must be GenerationAudit")
    if not isinstance(independent_audit_passed, bool) or not isinstance(candidate_beats_baseline, bool):
        raise ValueError("audit outcome flags must be boolean")
    if audit.decision is GenerationDecision.CONTINUE:
        raise ValueError("a running generation cannot be finalized")
    if audit.rollback_required or not independent_audit_passed:
        return GenerationAudit(audit.telemetry, audit.stop_reason, GenerationDecision.ROLLBACK_RESTART, False, True, audit.research_refresh_required)
    if audit.research_refresh_required or not candidate_beats_baseline:
        return GenerationAudit(audit.telemetry, audit.stop_reason, GenerationDecision.PLATEAU_RESEARCH_RESTART, False, False, True)
    return GenerationAudit(audit.telemetry, audit.stop_reason, GenerationDecision.PROMOTE_RESTART, True, False, False)
