from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class OutcomeStage(IntEnum):
    SIGNAL = 10
    QUALIFIED = 20
    CONVERSATION = 30
    RFQ = 40
    QUOTE = 50
    NEGOTIATION = 60
    ORDER = 70
    GROSS_MARGIN = 80
    REPEAT_BUSINESS = 90


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: str
    project_id: str
    stage: OutcomeStage
    evidence_refs: tuple[str, ...]
    decision_ref: str | None = None
    value_amount: float | None = None
    value_currency: str | None = None
    terminal: bool = False


@dataclass(frozen=True)
class OutcomeTransition:
    prior: OutcomeRecord
    candidate: OutcomeRecord
    allowed: bool
    reasons: tuple[str, ...]


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def validate_outcome(record: OutcomeRecord) -> tuple[str, ...]:
    reasons: list[str] = []
    if not isinstance(record, OutcomeRecord):
        return ("invalid outcome record",)
    if not all(_clean(x) for x in (record.outcome_id, record.project_id)):
        reasons.append("outcome_id/project_id invalid")
    if not isinstance(record.stage, OutcomeStage):
        reasons.append("invalid outcome stage")
    if not isinstance(record.evidence_refs, tuple) or not record.evidence_refs or any(not _clean(x) for x in record.evidence_refs):
        reasons.append("outcome requires evidence")
    elif len(set(record.evidence_refs)) != len(record.evidence_refs):
        reasons.append("outcome evidence references must be unique")
    if record.decision_ref is not None and not _clean(record.decision_ref):
        reasons.append("invalid decision_ref")
    if record.value_amount is not None:
        if not isinstance(record.value_amount, (int, float)) or isinstance(record.value_amount, bool):
            reasons.append("invalid value_amount")
        elif record.value_amount < 0:
            reasons.append("value_amount cannot be negative")
        if not _clean(record.value_currency):
            reasons.append("value_currency required when value_amount is present")
    elif record.value_currency is not None:
        reasons.append("value_currency requires value_amount")
    if not isinstance(record.terminal, bool):
        reasons.append("terminal must be boolean")
    return tuple(reasons)


def evaluate_outcome_transition(prior: OutcomeRecord, candidate: OutcomeRecord) -> OutcomeTransition:
    """Permit only evidence-linked, same-project outcome progress; never infer skipped terminal success."""
    reasons = list(validate_outcome(prior)) + list(validate_outcome(candidate))
    if reasons:
        return OutcomeTransition(prior, candidate, False, tuple(reasons))
    if prior.project_id != candidate.project_id:
        reasons.append("cross-project outcome transition blocked")
    if candidate.stage < prior.stage:
        reasons.append("outcome stage regression requires explicit loss/rollback record, not forward transition")
    if candidate.outcome_id == prior.outcome_id:
        reasons.append("candidate outcome_id must be new")
    if prior.terminal:
        reasons.append("terminal outcome cannot be silently advanced")
    if candidate.stage >= OutcomeStage.ORDER and candidate.decision_ref is None:
        reasons.append("order-or-later outcome requires a decision reference")
    return OutcomeTransition(prior, candidate, not reasons, tuple(reasons) if reasons else ("evidence-linked outcome transition",))
