from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Iterable


class EvidenceKind(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    ESTIMATE = "estimate"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"


class Capability(str, Enum):
    RESEARCH = "research"
    RETRIEVAL = "retrieval"
    MEMORY = "memory"
    PLANNING = "planning"
    TOOL_USE = "tool_use"
    VERIFICATION = "verification"
    RECOVERY = "recovery"
    EVALUATION = "evaluation"
    DRAFTING = "drafting"
    EXTERNAL_ACTION = "external_action"


class Risk(str, Enum):
    READ = "read"
    WRITE_LOCAL = "write_local"
    EXTERNAL = "external"
    IRREVERSIBLE = "irreversible"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    project_id: str
    statement: str
    kind: EvidenceKind
    source: str | None
    confidence: float

    def validate(self) -> None:
        if not self.evidence_id.strip() or not self.project_id.strip() or not self.statement.strip():
            raise ValueError("invalid_evidence_identity")
        if not 0 <= self.confidence <= 1:
            raise ValueError("invalid_confidence")
        if self.kind is EvidenceKind.FACT and not self.source:
            raise ValueError("fact_requires_source")


@dataclass(frozen=True)
class CapabilityProfile:
    capability: Capability
    tool_id: str
    provenance: str
    risk: Risk
    quality: float
    cost: float
    latency: float
    enabled: bool = True

    def score(self, *, max_risk: Risk) -> float:
        risk_order = {Risk.READ: 0, Risk.WRITE_LOCAL: 1, Risk.EXTERNAL: 2, Risk.IRREVERSIBLE: 3}
        if not self.enabled or risk_order[self.risk] > risk_order[max_risk]:
            return float("-inf")
        return round(self.quality * 0.70 - self.cost * 0.20 - self.latency * 0.10, 6)


@dataclass(frozen=True)
class Objective:
    objective_id: str
    project_id: str
    description: str
    required: tuple[Capability, ...]
    max_risk: Risk = Risk.READ
    acceptance_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanStep:
    capability: Capability
    tool_id: str
    reason: str
    score: float


@dataclass(frozen=True)
class ExecutionPlan:
    objective_id: str
    project_id: str
    steps: tuple[PlanStep, ...]
    blocked: tuple[Capability, ...]
    evidence_digest: str
    external_action_authorized: bool = False


@dataclass
class Outcome:
    objective_id: str
    passed: bool
    metrics: dict[str, float]
    failures: tuple[str, ...] = ()


@dataclass
class MetaAgent:
    tools: tuple[CapabilityProfile, ...]
    memory: dict[str, Evidence] = field(default_factory=dict)
    outcomes: list[Outcome] = field(default_factory=list)

    def remember(self, items: Iterable[Evidence]) -> None:
        for item in items:
            item.validate()
            existing = self.memory.get(item.evidence_id)
            if existing and existing != item:
                raise ValueError("evidence_id_collision")
            self.memory[item.evidence_id] = item

    def plan(self, objective: Objective) -> ExecutionPlan:
        if not objective.objective_id.strip() or not objective.project_id.strip():
            raise ValueError("invalid_objective_identity")
        if len(set(objective.required)) != len(objective.required):
            raise ValueError("duplicate_required_capability")

        project_evidence = sorted(
            (asdict(item) for item in self.memory.values() if item.project_id == objective.project_id),
            key=lambda item: item["evidence_id"],
        )
        digest = hashlib.sha256(
            json.dumps(project_evidence, ensure_ascii=False, sort_keys=True, default=str).encode()
        ).hexdigest()

        steps: list[PlanStep] = []
        blocked: list[Capability] = []
        for capability in objective.required:
            candidates = [tool for tool in self.tools if tool.capability is capability]
            ranked = sorted(
                ((tool.score(max_risk=objective.max_risk), tool) for tool in candidates),
                key=lambda pair: (-pair[0], pair[1].tool_id),
            )
            if not ranked or ranked[0][0] == float("-inf"):
                blocked.append(capability)
                continue
            score, selected = ranked[0]
            steps.append(
                PlanStep(
                    capability=capability,
                    tool_id=selected.tool_id,
                    reason=f"best_admissible:{selected.provenance}",
                    score=score,
                )
            )

        return ExecutionPlan(
            objective_id=objective.objective_id,
            project_id=objective.project_id,
            steps=tuple(steps),
            blocked=tuple(blocked),
            evidence_digest=digest,
            external_action_authorized=False,
        )

    def record_outcome(self, outcome: Outcome) -> None:
        if any(value < 0 for value in outcome.metrics.values()):
            raise ValueError("negative_metric")
        self.outcomes.append(outcome)

    def propose_improvement(self, objective_id: str) -> dict[str, object]:
        relevant = [item for item in self.outcomes if item.objective_id == objective_id]
        if not relevant:
            return {"disposition": "insufficient_evidence", "changes": []}
        failures = [failure for item in relevant if not item.passed for failure in item.failures]
        if not failures:
            return {"disposition": "retain_baseline", "changes": []}
        return {
            "disposition": "experiment_only",
            "changes": sorted(set(failures)),
            "requires_regression": True,
            "auto_promote": False,
        }


DEFAULT_CAPABILITY_PROFILES = (
    CapabilityProfile(Capability.RESEARCH, "authorized_web_research", "first_party", Risk.READ, 0.92, 0.30, 0.30),
    CapabilityProfile(Capability.RETRIEVAL, "connected_source_retrieval", "first_party", Risk.READ, 0.94, 0.20, 0.20),
    CapabilityProfile(Capability.MEMORY, "nexus_evidence_memory", "local", Risk.WRITE_LOCAL, 0.96, 0.10, 0.10),
    CapabilityProfile(Capability.PLANNING, "nexus_deterministic_planner", "local", Risk.READ, 0.93, 0.10, 0.10),
    CapabilityProfile(Capability.TOOL_USE, "nexus_runner_registry", "local", Risk.READ, 0.91, 0.10, 0.10),
    CapabilityProfile(Capability.VERIFICATION, "nexus_claim_verifier", "local", Risk.READ, 0.97, 0.20, 0.20),
    CapabilityProfile(Capability.RECOVERY, "nexus_forward_recovery", "local", Risk.WRITE_LOCAL, 0.90, 0.10, 0.20),
    CapabilityProfile(Capability.EVALUATION, "nexus_eval_harness", "local", Risk.READ, 0.95, 0.10, 0.10),
    CapabilityProfile(Capability.DRAFTING, "nexus_draft_lane", "local", Risk.WRITE_LOCAL, 0.91, 0.10, 0.10),
    CapabilityProfile(Capability.EXTERNAL_ACTION, "human_approval_gate", "local", Risk.EXTERNAL, 1.00, 0.10, 0.10),
)
