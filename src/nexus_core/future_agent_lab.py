from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Horizon = Literal["NOW", "NEAR", "MID", "LONG"]
Maturity = Literal["FACT", "CLAIM", "HYPOTHESIS"]
Decision = Literal["BUILD_NOW", "EXPERIMENT", "WATCH", "DEFER", "REJECT"]


@dataclass(frozen=True)
class FutureCapability:
    capability_id: str
    name: str
    horizon: Horizon
    maturity: Maturity
    problem: str
    architecture: str
    acceptance_test: str
    rollback: str
    project_refs: tuple[str, ...]
    safety_risk: int
    expected_leverage: int
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field in ("capability_id", "name", "problem", "architecture", "acceptance_test", "rollback"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} is required")
        for field in ("safety_risk", "expected_leverage"):
            value = getattr(self, field)
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{field} must be integer 0..5")
        if len(set(self.project_refs)) != len(self.project_refs):
            errors.append("duplicate project_refs")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            errors.append("duplicate evidence_refs")
        return tuple(errors)


def decide(item: FutureCapability) -> Decision:
    errors = item.validate()
    if errors:
        raise ValueError("invalid future capability: " + "; ".join(errors))
    if item.safety_risk >= 5 and item.maturity == "HYPOTHESIS":
        return "DEFER"
    if item.maturity == "FACT" and item.expected_leverage >= 4 and item.safety_risk <= 3:
        return "BUILD_NOW"
    if item.expected_leverage >= 4 and item.safety_risk <= 4:
        return "EXPERIMENT"
    if item.expected_leverage >= 3:
        return "WATCH"
    return "DEFER"


def portfolio() -> tuple[FutureCapability, ...]:
    return (
        FutureCapability(
            "FUT-PERSISTENT-EXEC", "Persistent executive agent", "NOW", "FACT",
            "Long-horizon business work loses continuity across sessions and tools.",
            "Canonical authority + durable task state + versioned memory + bounded tools + exact action gates.",
            "Resume a synthetic multi-day workflow after interruption with zero duplicate consequential action and preserved source/version state.",
            "Disable persistent runtime and fall back to current portfolio control + explicit tasks.",
            ("NEXUS_CORE",), 3, 5,
            ("openai-agents-sessions", "letta-stateful-agents"),
        ),
        FutureCapability(
            "FUT-SELF-LEARNING", "Experience-learning agent", "NEAR", "CLAIM",
            "Agents repeat mistakes because experience is not normalized into reusable, governed learning artifacts.",
            "Trajectory/event ledger -> evaluator -> versioned skill/memory proposal -> sandbox replay -> promote only after regression proof.",
            "On repeated frozen tasks, reduce human corrections without increasing policy/security/project-isolation failures.",
            "Revert skill/memory version and retain raw trajectories for audit.",
            ("NEXUS_CORE",), 4, 5,
            ("letta-trajectory", "context-bench-v2"),
        ),
        FutureCapability(
            "FUT-AGENT-MESH", "Agent mesh with protocol identity", "NEAR", "FACT",
            "Future systems will use heterogeneous agents and tools that need interoperable messaging and authorization.",
            "NEXUS authority plane + MCP/A2A adapters + agent identity + capability manifests + per-project policy envelopes.",
            "Route a synthetic task across two heterogeneous agents while preserving identity, provenance and policy with no privilege escalation.",
            "Disable mesh adapter and return to direct governed tool calls.",
            ("NEXUS_CORE",), 4, 4,
            ("mcp-2026-07-28", "a2a-protocol"),
        ),
        FutureCapability(
            "FUT-WORLD-MODEL", "Business world-model simulator", "MID", "HYPOTHESIS",
            "Executive decisions are made reactively instead of through scenario simulation across market, supplier, logistics and technical constraints.",
            "Evidence graph + causal assumptions + scenario generator + counterfactual evaluator + uncertainty labels; never direct authority.",
            "On historical held-out decisions, improve calibration or decision quality versus baseline without fabricating unsupported facts.",
            "Discard simulation layer; preserve source evidence and actual decision ledger.",
            ("NEXUS_CORE", "PRJ-HYD-01", "PRJ-KCL-01", "PRJ-CAN-01"), 4, 5,
        ),
        FutureCapability(
            "FUT-AUTONOMOUS-SCIENTIST", "Autonomous business/engineering scientist", "MID", "HYPOTHESIS",
            "Research is broad but hypotheses, experiments and evidence loops are still manually coordinated.",
            "Hypothesis generator -> evidence retrieval -> experiment design -> sandbox/test -> critic -> reproducibility gate -> knowledge proposal.",
            "Produce reproducible engineering/commercial experiments with retrievable evidence and zero unauthorized external action.",
            "Disable experiment proposer; retain reviewed evidence packets only.",
            ("NEXUS_CORE",), 4, 5,
        ),
        FutureCapability(
            "FUT-DIGITAL-TWIN", "Company digital twin", "LONG", "HYPOTHESIS",
            "Company decisions, assets, counterparties, projects and workflows are fragmented across systems.",
            "Versioned operational twin built from canonical project state, entity graph, event ledger, process models and permission-aware simulations.",
            "Replay selected historical periods and reproduce known state transitions while preserving supersession and access controls.",
            "Disable twin projections and retain canonical source registry + event ledger.",
            ("NEXUS_CORE",), 5, 5,
        ),
    )


def ranked_build_queue(items: Sequence[FutureCapability] | None = None) -> tuple[FutureCapability, ...]:
    candidates = tuple(portfolio() if items is None else items)
    for item in candidates:
        if item.validate():
            raise ValueError(item.capability_id + " invalid")
    weights = {"BUILD_NOW": 4, "EXPERIMENT": 3, "WATCH": 2, "DEFER": 1, "REJECT": 0}
    return tuple(sorted(candidates, key=lambda i: (-weights[decide(i)], -i.expected_leverage, i.safety_risk, i.capability_id)))
