"""Exploration lane for optional tools/plugins/apps.

Novel capabilities may be explored for unexpected value, but cannot become a
production dependency until a reversible experiment demonstrates measurable
benefit and security/privacy/cost constraints are acceptable.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExplorationDecision(str, Enum):
    EXPLORE = "explore"
    PILOT = "pilot"
    PROMOTE = "promote"
    REJECT = "reject"


@dataclass(frozen=True)
class CapabilityExperiment:
    capability_id: str
    novel_function: str
    reversible: bool
    measurable_success: bool
    handles_sensitive_data: bool
    permission_broadening: bool
    measured_gain: float | None = None


def evaluate_capability(experiment: CapabilityExperiment) -> ExplorationDecision:
    if not experiment.capability_id or not experiment.novel_function:
        return ExplorationDecision.REJECT
    if experiment.permission_broadening:
        return ExplorationDecision.EXPLORE
    if not experiment.reversible or not experiment.measurable_success:
        return ExplorationDecision.EXPLORE
    if experiment.measured_gain is None:
        return ExplorationDecision.PILOT
    if experiment.measured_gain > 0 and not experiment.handles_sensitive_data:
        return ExplorationDecision.PROMOTE
    return ExplorationDecision.REJECT
