from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from unicodedata import category


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
_MAX_ID_REF_LENGTH = 256
_MAX_TEXT_LENGTH = 4096
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


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


def _text_errors(
    field_name: str,
    value: object,
    *,
    max_length: int,
    reject_controls: bool = True,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, str):
        return [f"{field_name} must be a string"]
    if not value.strip():
        return [f"{field_name} is required"]
    if value != value.strip():
        errors.append(f"{field_name} cannot have leading or trailing whitespace")
    if len(value) > max_length:
        errors.append(f"{field_name} must be at most {max_length} characters")
    if reject_controls and any(category(ch) in _DISALLOWED_UNICODE_CATEGORIES for ch in value):
        errors.append(f"{field_name} cannot contain control or formatting characters")
    return errors


def _enum_error(field_name: str, value: object, allowed: set[str]) -> str | None:
    if not isinstance(value, str):
        return f"{field_name} must be a string"
    if value not in allowed:
        return f"{field_name} must be supported"
    return None


def _reference_errors(field_name: str, values: object) -> list[str]:
    if not isinstance(values, tuple):
        return [f"{field_name} must be a tuple"]
    if not values:
        return [f"{field_name} must contain at least one retrievable reference"]

    errors: list[str] = []
    seen: set[str] = set()
    duplicate_found = False
    for value in values:
        errors.extend(
            _text_errors(
                field_name,
                value,
                max_length=_MAX_ID_REF_LENGTH,
            )
        )
        if isinstance(value, str):
            if value in seen:
                duplicate_found = True
            seen.add(value)
    if duplicate_found:
        errors.append(f"{field_name} cannot contain duplicate references")
    return errors


def _optional_text_tuple_errors(field_name: str, values: object) -> list[str]:
    if not isinstance(values, tuple):
        return [f"{field_name} must be a tuple"]
    errors: list[str] = []
    for value in values:
        errors.extend(_text_errors(field_name, value, max_length=_MAX_TEXT_LENGTH))
    return errors


def _iso_time_errors(field_name: str, value: object, *, timezone_required: bool) -> list[str]:
    errors = _text_errors(field_name, value, max_length=_MAX_ID_REF_LENGTH)
    if errors or not isinstance(value, str):
        return errors
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return [f"{field_name} must be ISO-8601"]
    if timezone_required and parsed.tzinfo is None:
        errors.append(f"{field_name} must include a timezone offset")
    return errors


def validate_decision_chain(
    decision: DecisionRecord,
    observation: OutcomeObservation | None = None,
    evaluation: DecisionEvaluation | None = None,
) -> list[str]:
    """Validate a decision -> observation -> evaluation learning chain fail closed.

    This deliberately avoids uncalibrated numeric confidence scores. Runtime objects
    are treated as untrusted because Python type hints do not enforce types at runtime.
    """

    if not isinstance(decision, DecisionRecord):
        return ["decision must be a DecisionRecord"]
    if observation is not None and not isinstance(observation, OutcomeObservation):
        return ["observation must be an OutcomeObservation"]
    if evaluation is not None and not isinstance(evaluation, DecisionEvaluation):
        return ["evaluation must be a DecisionEvaluation"]

    errors: list[str] = []

    for name, value in (
        ("decision.decision_id", decision.decision_id),
        ("decision.subject", decision.subject),
        ("decision.decision", decision.decision),
        ("decision.rationale", decision.rationale),
        ("decision.expected_outcome", decision.expected_outcome),
        ("decision.success_criterion", decision.success_criterion),
    ):
        errors.extend(
            _text_errors(
                name,
                value,
                max_length=_MAX_ID_REF_LENGTH if name.endswith("decision_id") else _MAX_TEXT_LENGTH,
            )
        )
    errors.extend(_iso_time_errors("decision.review_at", decision.review_at, timezone_required=False))

    status_error = _enum_error("decision.status", decision.status, _ALLOWED_DECISION_STATUSES)
    if status_error:
        errors.append(status_error)

    errors.extend(_reference_errors("decision.evidence_refs", decision.evidence_refs))
    errors.extend(_optional_text_tuple_errors("decision.assumptions", decision.assumptions))
    errors.extend(_optional_text_tuple_errors("decision.unknowns", decision.unknowns))

    if observation is not None:
        for name, value in (
            ("observation.observation_id", observation.observation_id),
            ("observation.decision_id", observation.decision_id),
            ("observation.result", observation.result),
        ):
            errors.extend(
                _text_errors(
                    name,
                    value,
                    max_length=_MAX_ID_REF_LENGTH if name.endswith("_id") else _MAX_TEXT_LENGTH,
                )
            )
        errors.extend(
            _iso_time_errors(
                "observation.observed_at",
                observation.observed_at,
                timezone_required=True,
            )
        )

        kind_error = _enum_error(
            "observation.kind",
            observation.kind,
            _ALLOWED_EPISTEMIC_CLASSES,
        )
        if kind_error:
            errors.append(kind_error)

        if observation.decision_id != decision.decision_id:
            errors.append("observation.decision_id must match decision.decision_id")

        errors.extend(_reference_errors("observation.source_refs", observation.source_refs))

    if evaluation is not None:
        for name, value in (
            ("evaluation.evaluation_id", evaluation.evaluation_id),
            ("evaluation.decision_id", evaluation.decision_id),
            ("evaluation.observation_id", evaluation.observation_id),
            ("evaluation.learning", evaluation.learning),
            ("evaluation.next_action", evaluation.next_action),
        ):
            errors.extend(
                _text_errors(
                    name,
                    value,
                    max_length=_MAX_ID_REF_LENGTH if name.endswith("_id") else _MAX_TEXT_LENGTH,
                )
            )

        classification_error = _enum_error(
            "evaluation.classification",
            evaluation.classification,
            _ALLOWED_EVALUATION_CLASSES,
        )
        if classification_error:
            errors.append(classification_error)

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
