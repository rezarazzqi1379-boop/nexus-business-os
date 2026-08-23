from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentArchitecture(str, Enum):
    SINGLE_AGENT = "single_agent"
    CENTRALIZED_MULTI_AGENT = "centralized_multi_agent"
    PARALLEL_RESEARCH = "parallel_research"


@dataclass(frozen=True)
class ArchitectureSelectionInput:
    parallelizable_fraction: float
    sequential_dependency: float
    tool_count: int
    context_degradation: float
    independent_verification_available: bool
    latency_priority: float = 0.5
    cost_priority: float = 0.5


@dataclass(frozen=True)
class ArchitectureSelection:
    architecture: AgentArchitecture
    reasons: tuple[str, ...]
    max_workers: int


def _unit(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def select_agent_architecture(inp: ArchitectureSelectionInput) -> ArchitectureSelection:
    """Select the simplest architecture justified by task structure.

    Default is a single agent with a unified state. Multi-agent coordination is only
    admitted when decomposition is genuinely parallel, sequential coupling is low,
    and verification is available. Tool-heavy workflows are kept centralized because
    coordination overhead and divergent world state grow with tool count.
    """
    if not isinstance(inp, ArchitectureSelectionInput):
        raise TypeError("inp must be ArchitectureSelectionInput")
    for name in ("parallelizable_fraction", "sequential_dependency", "context_degradation", "latency_priority", "cost_priority"):
        if not _unit(getattr(inp, name)):
            raise ValueError(f"{name} must be within [0, 1]")
    if not isinstance(inp.tool_count, int) or isinstance(inp.tool_count, bool) or inp.tool_count < 0:
        raise ValueError("tool_count must be a non-negative integer")
    if not isinstance(inp.independent_verification_available, bool):
        raise ValueError("independent_verification_available must be boolean")

    reasons: list[str] = []

    # Strong sequential coupling is the clearest reason to avoid fragmented contexts.
    if inp.sequential_dependency >= 0.55:
        reasons.append("sequential dependency is high; preserve one integrated state and reasoning trajectory")
        return ArchitectureSelection(AgentArchitecture.SINGLE_AGENT, tuple(reasons), 1)

    # Tool-heavy environments magnify coordination/state divergence. Keep a single
    # controller unless the work is mostly independent research.
    if inp.tool_count >= 12 and inp.parallelizable_fraction < 0.8:
        reasons.append("tool count is high relative to decomposability; coordination tax likely exceeds benefit")
        return ArchitectureSelection(AgentArchitecture.SINGLE_AGENT, tuple(reasons), 1)

    # Parallel research can safely branch when workers only collect evidence and a
    # single synthesizer verifies/commits state. Workers never become authorities.
    if inp.parallelizable_fraction >= 0.8 and inp.sequential_dependency <= 0.25:
        if not inp.independent_verification_available:
            reasons.append("task is parallelizable but no independent verification is available")
            return ArchitectureSelection(AgentArchitecture.SINGLE_AGENT, tuple(reasons), 1)
        workers = 4 if inp.latency_priority >= inp.cost_priority else 2
        reasons.extend((
            "task decomposes into largely independent evidence-gathering branches",
            "a single verified synthesis point can prevent information-fragmentation from becoming authority",
        ))
        return ArchitectureSelection(AgentArchitecture.PARALLEL_RESEARCH, tuple(reasons), workers)

    # Centralized MAS is reserved for moderately parallel work where context pressure is
    # material and a verifier exists. This avoids independent-agent aggregation without
    # a validation bottleneck.
    if (
        inp.parallelizable_fraction >= 0.6
        and inp.sequential_dependency <= 0.4
        and inp.context_degradation >= 0.55
        and inp.independent_verification_available
    ):
        reasons.extend((
            "single-agent context utilization is materially degraded",
            "moderate parallel structure exists",
            "central verification is available to contain worker errors",
        ))
        return ArchitectureSelection(AgentArchitecture.CENTRALIZED_MULTI_AGENT, tuple(reasons), 3)

    reasons.append("no measured structural reason justifies multi-agent coordination")
    return ArchitectureSelection(AgentArchitecture.SINGLE_AGENT, tuple(reasons), 1)
