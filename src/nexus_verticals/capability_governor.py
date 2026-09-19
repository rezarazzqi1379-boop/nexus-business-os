"""Deterministic admission gate for NEXUS AI/tool capabilities.

The governor intentionally contains no model or network calls. It converts an
explicit evidence-backed scorecard and hard-gate status into a review decision.
Scores remain heuristic until calibrated against NEXUS benchmark outcomes.
"""

from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    TEST = "TEST"
    WATCH = "WATCH"
    REJECT = "REJECT"


@dataclass(frozen=True)
class CapabilityScore:
    marginal_benefit: int
    reliability_recoverability: int
    evidence_quality: int
    integration_fit: int
    observability_evaluation: int
    security_least_privilege: int
    cost_efficiency: int
    reversibility_lock_in: int
    learning_value: int

    LIMITS = {
        "marginal_benefit": 20,
        "reliability_recoverability": 15,
        "evidence_quality": 15,
        "integration_fit": 10,
        "observability_evaluation": 10,
        "security_least_privilege": 10,
        "cost_efficiency": 10,
        "reversibility_lock_in": 5,
        "learning_value": 5,
    }

    def __post_init__(self) -> None:
        for field, maximum in self.LIMITS.items():
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if not 0 <= value <= maximum:
                raise ValueError(f"{field} must be between 0 and {maximum}")

    @property
    def total(self) -> int:
        return sum(getattr(self, field) for field in self.LIMITS)


@dataclass(frozen=True)
class HardGates:
    evidence_verified: bool = False
    no_approval_bypass: bool = True
    no_unauthorized_external_action: bool = True
    no_credential_leakage: bool = True
    no_false_completion: bool = True
    no_cross_project_contamination: bool = True

    @property
    def passed(self) -> bool:
        return all(
            (
                self.evidence_verified,
                self.no_approval_bypass,
                self.no_unauthorized_external_action,
                self.no_credential_leakage,
                self.no_false_completion,
                self.no_cross_project_contamination,
            )
        )


def evaluate_capability(score: CapabilityScore, gates: HardGates) -> Decision:
    """Return the next admission state, never automatic production adoption.

    85+ means the candidate earns a smallest reversible TEST. Passing a score
    threshold alone never grants write authority or production promotion.
    """
    if not gates.passed:
        return Decision.REJECT
    if score.total >= 85:
        return Decision.TEST
    if score.total >= 70:
        return Decision.WATCH
    return Decision.REJECT
