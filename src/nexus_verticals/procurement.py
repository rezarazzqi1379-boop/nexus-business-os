from dataclasses import dataclass
from typing import Literal


OutcomeStatus = Literal["open", "won", "lost", "stalled"]


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    source_ref: str
    summary: str
    observed_at: str
    confidence: float


@dataclass(frozen=True)
class Relationship:
    relationship_id: str
    from_entity: str
    to_entity: str
    relationship_type: str
    status: str
    evidence_id: str


@dataclass(frozen=True)
class Signal:
    signal_id: str
    entity: str
    signal_type: str
    description: str
    evidence_id: str
    confidence: float


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    entity: str
    title: str
    stage: str
    signal_id: str
    next_action: str


@dataclass(frozen=True)
class Outcome:
    outcome_id: str
    opportunity_id: str
    outcome_type: str
    result: str
    status: OutcomeStatus = "open"
    terminal: bool = False


@dataclass(frozen=True)
class ProcurementVerticalRecord:
    case_id: str
    evidence: Evidence
    relationship: Relationship
    signal: Signal
    opportunity: Opportunity
    outcome: Outcome

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.case_id.strip():
            errors.append("case_id is required")

        for name, value in (
            ("evidence.confidence", self.evidence.confidence),
            ("signal.confidence", self.signal.confidence),
        ):
            if not 0 <= value <= 1:
                errors.append(f"{name} must be between 0 and 1")

        if self.relationship.evidence_id != self.evidence.evidence_id:
            errors.append("relationship.evidence_id must match evidence.evidence_id")

        if self.signal.evidence_id != self.evidence.evidence_id:
            errors.append("signal.evidence_id must match evidence.evidence_id")

        if self.opportunity.signal_id != self.signal.signal_id:
            errors.append("opportunity.signal_id must match signal.signal_id")

        if self.outcome.opportunity_id != self.opportunity.opportunity_id:
            errors.append("outcome.opportunity_id must match opportunity.opportunity_id")

        if self.relationship.to_entity != self.signal.entity:
            errors.append("relationship.to_entity must match signal.entity")

        if self.opportunity.entity != self.signal.entity:
            errors.append("opportunity.entity must match signal.entity")

        if self.outcome.terminal and self.outcome.status not in {"won", "lost"}:
            errors.append("terminal outcome must have status won or lost")

        if not self.outcome.terminal and self.outcome.status in {"won", "lost"}:
            errors.append("won/lost outcome must be terminal")

        return errors
