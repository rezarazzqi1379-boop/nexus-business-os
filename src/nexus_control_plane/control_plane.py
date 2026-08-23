from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Mapping, Optional, Set, Tuple

from nexus_control_plane.forge_preflight import (
    ForgePreflightRequest,
    PreflightDecision,
    evaluate_registered_forge_preflight,
)


class Maturity(str, Enum):
    DESIGNED = "designed"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    PRODUCTION = "production"


class Health(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class Authority(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    DRAFT = "draft"
    WRITE_STATE = "write_state"
    EXTERNAL_ACTION = "external_action"


class WorkState(str, Enum):
    CANDIDATE = "candidate"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"
    REJECTED = "rejected"


_MATERIAL_CHANGE_KINDS = {
    "agent_change",
    "architecture_change",
    "business_engine_change",
    "connector_change",
    "evaluator_change",
    "learning_change",
    "project_mechanism_change",
    "workflow_change",
}


def requires_forge_preflight(kind: object) -> bool:
    if not isinstance(kind, str):
        return False
    normalized = kind.strip()
    return normalized in _MATERIAL_CHANGE_KINDS or normalized.startswith("change:")


@dataclass(frozen=True)
class Goal:
    id: str
    name: str
    north_star_metric: str
    priority: int = 100


@dataclass
class AgentSpec:
    id: str
    role: str
    capabilities: Set[str]
    authorities: Set[Authority]
    maturity: Maturity = Maturity.DESIGNED
    health: Health = Health.HEALTHY
    version: str = "0.1.0"
    active: bool = True
    project_scopes: Set[str] = field(default_factory=lambda: {"*"})
    max_parallel_tasks: int = 1
    quality_score: float = 0.5
    cost_score: float = 0.5
    latency_score: float = 0.5


@dataclass
class WorkItem:
    id: str
    project_id: str
    goal_id: str
    kind: str
    required_capabilities: Set[str]
    required_authorities: Set[Authority]
    risk: int = 0
    value: int = 50
    urgency: int = 50
    evidence_quality: float = 0.0
    state: WorkState = WorkState.CANDIDATE
    depends_on: Tuple[str, ...] = ()
    dedupe_key: Optional[str] = None
    assigned_agent: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    forge_preflight: Optional[ForgePreflightRequest] = None


@dataclass(frozen=True)
class Evaluation:
    agent_id: str
    task_kind: str
    success: bool
    quality: float
    human_correction: bool = False
    policy_violation: bool = False
    notes: str = ""


@dataclass(frozen=True)
class ChangeProposal:
    agent_id: str
    from_version: str
    to_version: str
    rationale: str
    required_regressions: Tuple[str, ...]
    auto_promotable: bool = False


@dataclass
class ControlPlane:
    goals: Dict[str, Goal] = field(default_factory=dict)
    agents: Dict[str, AgentSpec] = field(default_factory=dict)
    work: Dict[str, WorkItem] = field(default_factory=dict)
    evaluations: List[Evaluation] = field(default_factory=list)
    completed_dedupe_keys: Set[str] = field(default_factory=set)
    running_by_agent: Dict[str, int] = field(default_factory=dict)

    def register_goal(self, goal: Goal) -> None:
        if goal.id in self.goals:
            raise ValueError(f"duplicate goal: {goal.id}")
        self.goals[goal.id] = goal

    def register_agent(self, agent: AgentSpec) -> None:
        if agent.id in self.agents:
            raise ValueError(f"duplicate agent: {agent.id}")
        self.agents[agent.id] = agent
        self.running_by_agent.setdefault(agent.id, 0)

    def submit(self, item: WorkItem) -> None:
        if item.id in self.work:
            raise ValueError(f"duplicate work id: {item.id}")
        if item.goal_id not in self.goals:
            raise ValueError(f"unknown goal: {item.goal_id}")

        if requires_forge_preflight(item.kind):
            if item.forge_preflight is None:
                item.state = WorkState.BLOCKED
                item.blockers.append("forge_preflight_required")
            else:
                result = evaluate_registered_forge_preflight(item.forge_preflight)
                if result.decision is PreflightDecision.BLOCK:
                    item.state = WorkState.BLOCKED
                    item.blockers.extend(f"forge_block:{reason}" for reason in result.blockers)
                elif result.decision is PreflightDecision.HOLD:
                    item.state = WorkState.REVIEW
                    item.blockers.extend(f"forge_hold:{reason}" for reason in result.warnings)
                elif result.decision is PreflightDecision.SHADOW_READY:
                    item.state = WorkState.READY

        if item.dedupe_key and item.dedupe_key in self.completed_dedupe_keys:
            item.state = WorkState.REJECTED
            item.blockers.append("duplicate_of_completed_action")
        self.work[item.id] = item

    def _deps_done(self, item: WorkItem) -> bool:
        return all(self.work.get(dep) and self.work[dep].state == WorkState.DONE for dep in item.depends_on)

    def _scope_ok(self, agent: AgentSpec, project_id: str) -> bool:
        return "*" in agent.project_scopes or project_id in agent.project_scopes

    def _eligible(self, agent: AgentSpec, item: WorkItem) -> bool:
        if not agent.active or agent.health == Health.OFFLINE:
            return False
        if self.running_by_agent.get(agent.id, 0) >= agent.max_parallel_tasks:
            return False
        if not self._scope_ok(agent, item.project_id):
            return False
        if not item.required_capabilities.issubset(agent.capabilities):
            return False
        if not item.required_authorities.issubset(agent.authorities):
            return False
        if Authority.EXTERNAL_ACTION in item.required_authorities:
            return False
        return True

    def _score(self, agent: AgentSpec, item: WorkItem) -> float:
        maturity_bonus = {
            Maturity.DESIGNED: 0.0,
            Maturity.IMPLEMENTED: 0.05,
            Maturity.TESTED: 0.15,
            Maturity.PRODUCTION: 0.20,
        }[agent.maturity]
        health_penalty = 0.20 if agent.health == Health.DEGRADED else 0.0
        return (
            0.45 * agent.quality_score
            + 0.20 * (1 - agent.cost_score)
            + 0.15 * (1 - agent.latency_score)
            + 0.20 * (item.value / 100)
            + maturity_bonus
            - health_penalty
        )

    def route(self, item_id: str) -> Optional[str]:
        item = self.work[item_id]
        if item.state in {WorkState.BLOCKED, WorkState.REVIEW}:
            return None
        if item.state in {WorkState.DONE, WorkState.REJECTED, WorkState.RUNNING}:
            return item.assigned_agent
        if not self._deps_done(item):
            item.state = WorkState.BLOCKED
            if "dependency_not_done" not in item.blockers:
                item.blockers.append("dependency_not_done")
            return None
        eligible = [a for a in self.agents.values() if self._eligible(a, item)]
        if not eligible:
            item.state = WorkState.BLOCKED
            reason = (
                "requires_human_approval_gateway"
                if Authority.EXTERNAL_ACTION in item.required_authorities
                else "no_eligible_agent"
            )
            if reason not in item.blockers:
                item.blockers.append(reason)
            return None
        selected = max(eligible, key=lambda a: self._score(a, item))
        item.assigned_agent = selected.id
        item.state = WorkState.RUNNING
        self.running_by_agent[selected.id] = self.running_by_agent.get(selected.id, 0) + 1
        return selected.id

    def complete(self, item_id: str, *, success: bool, quality: float, human_correction: bool = False,
                 policy_violation: bool = False, notes: str = "") -> None:
        item = self.work[item_id]
        if item.assigned_agent:
            self.running_by_agent[item.assigned_agent] = max(0, self.running_by_agent.get(item.assigned_agent, 0) - 1)
            self.evaluations.append(Evaluation(
                agent_id=item.assigned_agent,
                task_kind=item.kind,
                success=success,
                quality=quality,
                human_correction=human_correction,
                policy_violation=policy_violation,
                notes=notes,
            ))
        item.state = WorkState.DONE if success and not policy_violation else WorkState.REVIEW
        if item.state == WorkState.DONE and item.dedupe_key:
            self.completed_dedupe_keys.add(item.dedupe_key)

    def conflicts(self) -> List[str]:
        issues: List[str] = []
        seen: Dict[str, str] = {}
        for item in self.work.values():
            if not item.dedupe_key or item.state in {WorkState.REJECTED, WorkState.DONE}:
                continue
            previous = seen.get(item.dedupe_key)
            if previous:
                issues.append(f"duplicate_active_work:{previous}:{item.id}:{item.dedupe_key}")
            else:
                seen[item.dedupe_key] = item.id
        for agent in self.agents.values():
            if Authority.EXTERNAL_ACTION in agent.authorities and Authority.WRITE_STATE not in agent.authorities:
                issues.append(f"authority_shape_suspicious:{agent.id}")
        return issues

    def agent_health_report(self) -> Dict[str, Mapping[str, object]]:
        return {
            agent.id: {
                "role": agent.role,
                "health": agent.health.value,
                "maturity": agent.maturity.value,
                "version": agent.version,
                "active": agent.active,
                "running": self.running_by_agent.get(agent.id, 0),
            }
            for agent in self.agents.values()
        }

    def improvement_proposals(self, min_samples: int = 3) -> List[ChangeProposal]:
        grouped: Dict[str, List[Evaluation]] = {}
        for e in self.evaluations:
            grouped.setdefault(e.agent_id, []).append(e)
        proposals: List[ChangeProposal] = []
        for agent_id, samples in grouped.items():
            if len(samples) < min_samples or agent_id not in self.agents:
                continue
            avg_quality = sum(e.quality for e in samples) / len(samples)
            correction_rate = sum(e.human_correction for e in samples) / len(samples)
            violations = sum(e.policy_violation for e in samples)
            success_rate = sum(e.success for e in samples) / len(samples)
            if violations or avg_quality < 0.75 or correction_rate > 0.25 or success_rate < 0.80:
                agent = self.agents[agent_id]
                proposals.append(ChangeProposal(
                    agent_id=agent_id,
                    from_version=agent.version,
                    to_version=self._next_patch(agent.version),
                    rationale=(
                        f"quality={avg_quality:.2f}; success={success_rate:.2f}; "
                        f"human_correction={correction_rate:.2f}; policy_violations={violations}"
                    ),
                    required_regressions=(
                        "duplicate_outreach",
                        "unsupported_claim",
                        "cross_project_contamination",
                        "approval_bypass",
                        "false_completion",
                    ),
                    auto_promotable=False,
                ))
        return proposals

    @staticmethod
    def _next_patch(version: str) -> str:
        major, minor, patch = (int(x) for x in version.split("."))
        return f"{major}.{minor}.{patch + 1}"
