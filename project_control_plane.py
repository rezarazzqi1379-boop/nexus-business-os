"""NEXUS project control plane.

Turns a durable project objective into one auditable coordination plan.  The
module deliberately plans work; it does not install tools, grant credentials,
or execute external side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping

from execution_scheduler import ExecutionLane, ExecutionSchedule, schedule_execution
from source_failover import SourceHealth, SourceRoute, route_read_sources
from src.nexus_core.agent_catalog import AgentCatalogEntry, candidates_for_problem, seed_catalog
from conversation_control import (
    ConversationSnapshot, IdeaProposal, ProjectNeed, TokenAllocation, TokenPolicy,
    allocate_tokens, discover_needs, propose_ideas,
)

Risk = Literal["read", "local_write", "external"]
CONTROL_PLANE_VERSION = "nexus.project-control-plane.v1"
_EXECUTION_READY_LIFECYCLES = frozenset({"PILOT", "ADOPTED_ADAPTER"})
_SANDBOX_ONLY_LIFECYCLES = frozenset({"SANDBOX_READY", "EXPERIMENT"})


@dataclass(frozen=True)
class WorkRequest:
    work_id: str
    project_id: str
    objective: str
    problem_tags: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    lane: str = "research"
    risk: Risk = "read"
    priority: int = 3
    urgency: int = 3
    evidence_readiness: int = 3
    reversible: bool = True

    def validate(self) -> None:
        if not self.work_id.strip() or not self.project_id.strip() or not self.objective.strip():
            raise ValueError("invalid_work_identity")
        if not self.problem_tags or not self.required_capabilities:
            raise ValueError("routing_requirements_required")
        if len(set(self.problem_tags)) != len(self.problem_tags):
            raise ValueError("duplicate_problem_tags")
        if len(set(self.required_capabilities)) != len(self.required_capabilities):
            raise ValueError("duplicate_required_capabilities")
        if self.risk not in {"read", "local_write", "external"}:
            raise ValueError("invalid_risk")
        for value in (self.priority, self.urgency, self.evidence_readiness):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
                raise ValueError("invalid_work_score")


@dataclass(frozen=True)
class AgentAssignment:
    work_id: str
    agent_id: str
    matched_capabilities: tuple[str, ...]
    lifecycle: str


@dataclass(frozen=True)
class CoordinationPlan:
    version: str
    assignments: tuple[AgentAssignment, ...]
    source_routes: Mapping[str, SourceRoute]
    schedule: ExecutionSchedule
    approval_required: tuple[str, ...]
    blocked: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class PortfolioCycle:
    token_allocation: TokenAllocation
    needs: tuple[ProjectNeed, ...]
    ideas: tuple[IdeaProposal, ...]
    coordination: CoordinationPlan


def _select_agent(request: WorkRequest, catalog: tuple[AgentCatalogEntry, ...]) -> AgentAssignment | None:
    candidates: dict[str, AgentCatalogEntry] = {}
    for tag in request.problem_tags:
        for item in candidates_for_problem(catalog, tag):
            candidates[item.catalog_id] = item
    required = set(request.required_capabilities)
    eligible = {
        catalog_id: item for catalog_id, item in candidates.items()
        if item.lifecycle in _EXECUTION_READY_LIFECYCLES
        or (
            item.lifecycle in _SANDBOX_ONLY_LIFECYCLES
            and request.lane == "sandbox"
            and request.risk != "external"
        )
    }
    ranked = sorted(
        eligible.values(),
        key=lambda item: (-len(required.intersection(item.capabilities)), item.catalog_id),
    )
    if not ranked:
        return None
    best = ranked[0]
    matched = tuple(sorted(required.intersection(best.capabilities)))
    if not matched:
        return None
    return AgentAssignment(request.work_id, best.catalog_id, matched, best.lifecycle)


def build_coordination_plan(
    requests: Iterable[WorkRequest],
    sources: Iterable[SourceHealth],
    *,
    catalog: tuple[AgentCatalogEntry, ...] | None = None,
    concurrency: int = 4,
    max_sources_per_work: int = 3,
    max_source_cost_per_work: float = 0.0,
) -> CoordinationPlan:
    """Build a fail-closed multi-project plan without performing external work."""
    work = tuple(requests)
    source_snapshot = tuple(sources)
    if not work:
        raise ValueError("at_least_one_work_request_required")
    seen: set[str] = set()
    for item in work:
        item.validate()
        if item.work_id in seen:
            raise ValueError("duplicate_work_id")
        seen.add(item.work_id)

    available_catalog = catalog if catalog is not None else seed_catalog()
    assignments: list[AgentAssignment] = []
    blocked: list[tuple[str, str]] = []
    approval_required: list[str] = []
    routes: dict[str, SourceRoute] = {}
    lanes: list[ExecutionLane] = []

    for item in work:
        assignment = _select_agent(item, available_catalog)
        if assignment is None:
            blocked.append((item.work_id, "no_qualified_agent"))
            state = "blocked"
        else:
            assignments.append(assignment)
            state = "ready"

        if item.lane == "research":
            route = route_read_sources(
                source_snapshot,
                max_sources=max_sources_per_work,
                max_cost=max_source_cost_per_work,
            )
            routes[item.work_id] = route
            if not route.selected:
                blocked.append((item.work_id, "no_safe_read_source"))
                state = "blocked"

        if item.risk == "external":
            approval_required.append(item.work_id)
            state = "blocked"

        lanes.append(ExecutionLane(
            item.work_id, item.project_id, item.lane, state,
            item.priority, item.urgency, item.evidence_readiness,
            0 if item.risk == "read" else (2 if item.risk == "local_write" else 5),
            item.reversible,
        ))

    return CoordinationPlan(
        CONTROL_PLANE_VERSION,
        tuple(assignments),
        routes,
        schedule_execution(lanes, concurrency=concurrency),
        tuple(sorted(approval_required)),
        tuple(sorted(set(blocked))),
    )


def build_portfolio_cycle(
    snapshots: Iterable[ConversationSnapshot],
    sources: Iterable[SourceHealth],
    *,
    now: int,
    estimated_history_tokens: int,
    estimated_evidence_tokens: int,
    token_policy: TokenPolicy = TokenPolicy(),
    max_ideas: int = 10,
    concurrency: int = 4,
) -> PortfolioCycle:
    """Run metadata -> needs -> ideas -> governed execution-plan in one pass."""
    allocation = allocate_tokens(
        token_policy,
        estimated_history=estimated_history_tokens,
        estimated_evidence=estimated_evidence_tokens,
    )
    needs = discover_needs(tuple(snapshots), now=now)
    ideas = propose_ideas(needs, max_ideas=max_ideas)
    if not ideas:
        raise ValueError("no_actionable_portfolio_needs")
    need_by_id = {need.need_id: need for need in needs}
    requests = []
    for idea in ideas:
        need = need_by_id[idea.need_id]
        requests.append(WorkRequest(
            work_id=idea.idea_id,
            project_id=need.project_id,
            objective=idea.smallest_experiment,
            problem_tags=("agent-runtime",),
            required_capabilities=("agents",),
            lane="research",
            risk="read",
            priority=min(5, need.leverage),
            urgency=min(5, need.urgency),
            evidence_readiness=max(1, round(need.confidence * 5)),
            reversible=True,
        ))
    coordination = build_coordination_plan(
        requests, tuple(sources), concurrency=concurrency,
    )
    return PortfolioCycle(allocation, needs, ideas, coordination)
