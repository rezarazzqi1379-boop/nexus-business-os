from dataclasses import dataclass
from typing import Literal


EpistemicClass = Literal[
    "fact",
    "claim",
    "estimate",
    "inference",
    "hypothesis",
    "assumption",
    "unknown",
]
DecisionStatus = Literal["planned", "active", "evaluated", "cancelled"]
EvaluationClass = Literal[
    "confirmed",
    "partially_confirmed",
    "disconfirmed",
    "inconclusive",
]

_ALLOWED_EPISTEMIC_CLASSES = {
    "fact",
    "claim",
    "estimate",
    "inference",
    "hypothesis",
    "assumption",
    "unknown",
}
_ALLOWED_DECISION_STATUSES = {"planned", "active", "evaluated", "cancelled"}
_ALLOWED_EVALUATION_CLASSES = {
    "confirmed",
    "partially_confirmed",
    "disconfirmed",
    "inconclusive",
}


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    subject: str
    decision: str
    rationale: str
    expected_outcome: str
    success_criterion: str
    review_at: str
    evidence_refs: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    status: DecisionStatus = "planned"


@dataclass(frozen=True)
class OutcomeObservation:
    observation_id: str
    decision_id: str
    observed_at: str
    result: str
    source_refs: tuple[str, ...]
    kind: EpistemicClass


@dataclass(frozen=True)
class DecisionEvaluation:
    evaluation_id: str
    decision_id: str
    observation_id: str
    classification: EvaluationClass
    learning: str
    next_action: str


def validate_decision_chain(
    decision: DecisionRecord,
    observation: OutcomeObservation | None = None,
    evaluation: DecisionEvaluation | None = None,
) -> list[str]:
    """Validate a decision -> observation -> evaluation learning chain."""
    errors: list[str] = []

    required_decision_values = (
        ("decision.decision_id", decision.decision_id),
        ("decision.subject", decision.subject),
        ("decision.decision", decision.decision),
        ("decision.rationale", decision.rationale),
        ("decision.expected_outcome", decision.expected_outcome),
        ("decision.success_criterion", decision.success_criterion),
        ("decision.review_at", decision.review_at),
    )
    for name, value in required_decision_values:
        if not value.strip():
            errors.append(f"{name} is required")

    if decision.status not in _ALLOWED_DECISION_STATUSES:
        errors.append("decision.status must be supported")

    if not decision.evidence_refs:
        errors.append("decision.evidence_refs must contain at least one retrievable reference")
    elif any(not ref.strip() for ref in decision.evidence_refs):
        errors.append("decision.evidence_refs cannot contain blank references")

    if observation is not None:
        required_observation_values = (
            ("observation.observation_id", observation.observation_id),
            ("observation.decision_id", observation.decision_id),
            ("observation.observed_at", observation.observed_at),
            ("observation.result", observation.result),
            ("observation.kind", observation.kind),
        )
        for name, value in required_observation_values:
            if not value.strip():
                errors.append(f"{name} is required")

        if observation.kind not in _ALLOWED_EPISTEMIC_CLASSES:
            errors.append("observation.kind must be a supported epistemic class")
        if observation.decision_id != decision.decision_id:
            errors.append("observation.decision_id must match decision.decision_id")
        if not observation.source_refs:
            errors.append("observation.source_refs must contain at least one retrievable reference")
        elif any(not ref.strip() for ref in observation.source_refs):
            errors.append("observation.source_refs cannot contain blank references")

    if evaluation is not None:
        required_evaluation_values = (
            ("evaluation.evaluation_id", evaluation.evaluation_id),
            ("evaluation.decision_id", evaluation.decision_id),
            ("evaluation.observation_id", evaluation.observation_id),
            ("evaluation.classification", evaluation.classification),
            ("evaluation.learning", evaluation.learning),
            ("evaluation.next_action", evaluation.next_action),
        )
        for name, value in required_evaluation_values:
            if not value.strip():
                errors.append(f"{name} is required")

        if evaluation.classification not in _ALLOWED_EVALUATION_CLASSES:
            errors.append("evaluation.classification must be supported")
        if observation is None:
            errors.append("evaluation requires an observation")
        else:
            if evaluation.decision_id != decision.decision_id:
                errors.append("evaluation.decision_id must match decision.decision_id")
            if evaluation.observation_id != observation.observation_id:
                errors.append("evaluation.observation_id must match observation.observation_id")

    if decision.status == "evaluated":
        if observation is None:
            errors.append("evaluated decision requires an observation")
        if evaluation is None:
            errors.append("evaluated decision requires an evaluation")
    if decision.status in {"planned", "active"} and evaluation is not None:
        errors.append("planned/active decision cannot already have a final evaluation")
    if decision.status == "cancelled" and evaluation is not None:
        errors.append("cancelled decision cannot have an outcome evaluation")

    return errors
