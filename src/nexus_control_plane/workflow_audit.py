from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean


class AuditSignal(str, Enum):
    REWORK = "rework"
    DUPLICATE = "duplicate"
    BLOCKER_LATE = "blocker_late"
    HANDOFF_DELAY = "handoff_delay"
    LOW_EVIDENCE = "low_evidence"
    UNOBSERVED = "unobserved"


class ImprovementAction(str, Enum):
    KEEP = "keep"
    RESEARCH = "research"
    ADD_GATE = "add_gate"
    AUTOMATE = "automate"
    SIMPLIFY = "simplify"
    RETIRE = "retire"


@dataclass(frozen=True)
class WorkflowObservation:
    workflow_id: str
    project_id: str
    duration_minutes: float | None
    manual_touch_count: int | None
    rework_count: int | None
    duplicate_count: int | None
    blocker_discovered_after_outreach: bool | None
    evidence_complete: bool | None
    outcome_observed: bool

    def validate(self) -> None:
        if not self.workflow_id or self.workflow_id.strip() != self.workflow_id:
            raise ValueError("workflow_id must be canonical")
        if not self.project_id or self.project_id.strip() != self.project_id:
            raise ValueError("project_id must be canonical")
        for value, name in (
            (self.duration_minutes, "duration_minutes"),
            (self.manual_touch_count, "manual_touch_count"),
            (self.rework_count, "rework_count"),
            (self.duplicate_count, "duplicate_count"),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class WorkflowAuditResult:
    workflow_id: str
    projects_observed: int
    observations: int
    mean_duration_minutes: float | None
    mean_manual_touches: float | None
    rework_rate: float | None
    duplicate_rate: float | None
    late_blocker_rate: float | None
    evidence_gap_rate: float | None
    recommendation: ImprovementAction
    reasons: tuple[str, ...]


def _rate(values: list[bool]) -> float | None:
    return None if not values else sum(values) / len(values)


def audit_workflow(observations: tuple[WorkflowObservation, ...]) -> WorkflowAuditResult:
    if not observations:
        raise ValueError("at least one observation is required")
    for obs in observations:
        obs.validate()

    workflow_ids = {obs.workflow_id for obs in observations}
    if len(workflow_ids) != 1:
        raise ValueError("audit requires a single workflow_id")
    workflow_id = next(iter(workflow_ids))

    durations = [obs.duration_minutes for obs in observations if obs.duration_minutes is not None]
    touches = [obs.manual_touch_count for obs in observations if obs.manual_touch_count is not None]
    reworks = [obs.rework_count > 0 for obs in observations if obs.rework_count is not None]
    duplicates = [obs.duplicate_count > 0 for obs in observations if obs.duplicate_count is not None]
    late_blockers = [obs.blocker_discovered_after_outreach for obs in observations if obs.blocker_discovered_after_outreach is not None]
    evidence_gaps = [not obs.evidence_complete for obs in observations if obs.evidence_complete is not None]

    rework_rate = _rate(reworks)
    duplicate_rate = _rate(duplicates)
    late_blocker_rate = _rate(late_blockers)
    evidence_gap_rate = _rate(evidence_gaps)

    reasons: list[str] = []
    recommendation = ImprovementAction.KEEP

    # Decision rules are deliberately ordinal and evidence-bounded.
    # Missing observations never become synthetic zeroes.
    if late_blocker_rate is not None and late_blocker_rate >= 0.34:
        recommendation = ImprovementAction.ADD_GATE
        reasons.append("late decision-critical blockers recur; add or strengthen a pre-action readiness gate")
    if rework_rate is not None and rework_rate >= 0.50:
        if recommendation is ImprovementAction.KEEP:
            recommendation = ImprovementAction.SIMPLIFY
        reasons.append("rework is frequent; reduce ambiguity or split the workflow")
    if duplicate_rate is not None and duplicate_rate >= 0.20:
        if recommendation is ImprovementAction.KEEP:
            recommendation = ImprovementAction.ADD_GATE
        reasons.append("duplicate work recurs; strengthen idempotency and duplicate checks")
    if evidence_gap_rate is not None and evidence_gap_rate >= 0.34:
        if recommendation is ImprovementAction.KEEP:
            recommendation = ImprovementAction.RESEARCH
        reasons.append("evidence gaps recur; improve source acquisition before automation")

    comparable_outcomes = [obs for obs in observations if obs.outcome_observed]
    if len({obs.project_id for obs in comparable_outcomes}) >= 3 and len(comparable_outcomes) >= 5:
        if recommendation is ImprovementAction.KEEP and touches and mean(touches) >= 4:
            recommendation = ImprovementAction.AUTOMATE
            reasons.append("stable cross-project workflow with repeated manual touches is an automation candidate")

    if not reasons:
        reasons.append("no recurring measured failure pattern crosses the current intervention thresholds")

    return WorkflowAuditResult(
        workflow_id=workflow_id,
        projects_observed=len({obs.project_id for obs in observations}),
        observations=len(observations),
        mean_duration_minutes=mean(durations) if durations else None,
        mean_manual_touches=mean(touches) if touches else None,
        rework_rate=rework_rate,
        duplicate_rate=duplicate_rate,
        late_blocker_rate=late_blocker_rate,
        evidence_gap_rate=evidence_gap_rate,
        recommendation=recommendation,
        reasons=tuple(reasons),
    )
