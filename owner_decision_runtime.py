"""Bounded owner-delegation for reversible NEXUS decisions.

The engine may choose research, tests, evidence recording and reversible local
edits. It cannot turn a broad mandate into external, identity, payment,
credential, production, publish, deploy or merge authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

from execution_scheduler import ExecutionLane, ExecutionSchedule, schedule_execution
from policy import decide_action
from projects import ProjectPolicy
from unified_data_environment import EvidenceObservation, UnifiedDataHub

DecisionState = Literal["SELECTED", "QUEUED", "WAITING_APPROVAL", "DENIED"]


def _digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class DelegationMandate:
    mandate_id: str
    project_scope: tuple[str, ...]
    allowed_actions: tuple[str, ...] = (
        "read", "classify", "research", "compare", "draft", "test", "summarize",
        "local_edit", "sandbox_experiment", "record_evidence", "local_backup",
    )
    max_risk: int = 2
    max_cost_microusd: int = 0
    allow_external_actions: bool = False
    allow_authority_expansion: bool = False

    def validate(self) -> None:
        if not self.mandate_id.strip() or not self.project_scope:
            raise ValueError("invalid_delegation_mandate")
        if not 0 <= self.max_risk <= 5 or self.max_cost_microusd < 0:
            raise ValueError("invalid_delegation_limits")
        if self.allow_external_actions or self.allow_authority_expansion:
            raise ValueError("broad_mandate_cannot_grant_consequential_authority")


@dataclass(frozen=True)
class DecisionOption:
    decision_id: str
    project_id: str
    action: str
    objective: str
    evidence_refs: tuple[str, ...]
    expected_value: int
    urgency: int
    evidence_readiness: int
    risk: int
    reversible: bool
    estimated_cost_microusd: int = 0

    def validate(self) -> None:
        if not all(x.strip() for x in (self.decision_id, self.project_id, self.action, self.objective)):
            raise ValueError("invalid_decision_identity")
        if not self.evidence_refs or any(not x.strip() for x in self.evidence_refs):
            raise ValueError("decision_evidence_required")
        if any(isinstance(x, bool) or not isinstance(x, int) or not 0 <= x <= 5
               for x in (self.expected_value, self.urgency, self.evidence_readiness, self.risk)):
            raise ValueError("invalid_decision_score")
        if self.estimated_cost_microusd < 0:
            raise ValueError("invalid_decision_cost")


@dataclass(frozen=True)
class DecisionResult:
    decision_id: str
    state: DecisionState
    reason: str


@dataclass(frozen=True)
class DelegatedDecisionCycle:
    mandate_id: str
    results: tuple[DecisionResult, ...]
    schedule: ExecutionSchedule
    external_actions_executed: bool = False
    authority_expanded: bool = False


def decide_for_owner(options: tuple[DecisionOption, ...], mandate: DelegationMandate,
                     *, concurrency: int = 4) -> DelegatedDecisionCycle:
    mandate.validate()
    seen: set[str] = set()
    eligible: list[DecisionOption] = []
    results: list[DecisionResult] = []
    for option in options:
        option.validate()
        if option.decision_id in seen:
            raise ValueError("duplicate_decision_id")
        seen.add(option.decision_id)
        policy = decide_action(option.action)
        reason = ""
        state: DecisionState | None = None
        if option.project_id not in mandate.project_scope:
            state, reason = "DENIED", "outside_project_scope"
        elif option.action not in mandate.allowed_actions:
            state, reason = ("WAITING_APPROVAL", "action_not_delegated") if policy.disposition == "approval_required" else ("DENIED", "action_not_delegated")
        elif policy.disposition == "approval_required":
            state, reason = "WAITING_APPROVAL", "exact_scope_human_approval_required"
        elif policy.disposition != "allow":
            state, reason = "DENIED", "policy_denied"
        elif not option.reversible:
            state, reason = "WAITING_APPROVAL", "irreversible_action_requires_owner"
        elif option.risk > mandate.max_risk:
            state, reason = "WAITING_APPROVAL", "risk_exceeds_delegated_limit"
        elif option.estimated_cost_microusd > mandate.max_cost_microusd:
            state, reason = "WAITING_APPROVAL", "cost_exceeds_delegated_limit"
        if state:
            results.append(DecisionResult(option.decision_id, state, reason))
        else:
            eligible.append(option)

    lanes = tuple(ExecutionLane(x.decision_id, x.project_id, "research" if x.action == "research" else "engineering",
                                "ready", x.expected_value, x.urgency, x.evidence_readiness,
                                x.risk, x.reversible) for x in eligible)
    schedule = schedule_execution(lanes, concurrency=concurrency)
    running = set(schedule.running)
    for option in eligible:
        results.append(DecisionResult(option.decision_id,
                                      "SELECTED" if option.decision_id in running else "QUEUED",
                                      "highest_safe_expected_value" if option.decision_id in running else "safe_but_concurrency_queued"))
    results.sort(key=lambda x: x.decision_id)
    return DelegatedDecisionCycle(mandate.mandate_id, tuple(results), schedule, False, False)


def options_for_portfolio(projects: tuple[ProjectPolicy, ...]) -> tuple[DecisionOption, ...]:
    """Generate one safe next decision per project from canonical policy metadata."""
    options = []
    for project in projects:
        action = "summarize" if project.status == "hold" else ("draft" if project.status == "blocked" else "research")
        objective = (f"Preserve hold status and summarize evidence for {project.project_id}" if project.status == "hold"
                     else f"Resolve next evidence gap for {project.project_id}: {project.next_evidence[0]}")
        options.append(DecisionOption(
            f"portfolio-{project.project_id}-{action}", project.project_id, action, objective,
            (f"projects.py:{project.project_id}",), min(5, max(1, project.priority // 20)),
            5 if project.status in {"active", "blocked"} else 2, 3, 0, True, 0))
    return tuple(options)


def record_decision_cycle(hub: UnifiedDataHub, cycle: DelegatedDecisionCycle,
                          *, project_id: str, observed_at: str) -> bool:
    digest = _digest(asdict(cycle))
    selected = tuple(x.decision_id for x in cycle.results if x.state == "SELECTED")
    refs = tuple(f"decision:{x.decision_id}:{x.state}" for x in cycle.results)
    return hub.record_observation(EvidenceObservation(
        f"delegated-decision-{digest[:20]}", project_id, "OWNER_DELEGATED_DECISION",
        f"selected {len(selected)} reversible local decisions; no external action or authority expansion",
        refs, observed_at, 1.0))
