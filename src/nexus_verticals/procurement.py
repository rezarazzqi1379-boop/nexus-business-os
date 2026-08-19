from dataclasses import dataclass


@dataclass
class Evidence:
    source: str
    source_ref: str
    summary: str
    observed_at: str
    confidence: float


@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    relationship_type: str
    status: str
    evidence_ref: str


@dataclass
class Signal:
    entity: str
    signal_type: str
    description: str
    evidence_ref: str
    confidence: float


@dataclass
class Opportunity:
    entity: str
    title: str
    stage: str
    signal_ref: str
    next_action: str


@dataclass
class Outcome:
    opportunity_ref: str
    outcome_type: str
    result: str
    terminal: bool = False


@dataclass
class ProcurementVerticalRecord:
    case_id: str
    evidence: Evidence
    relationship: Relationship
    signal: Signal
    opportunity: Opportunity
    outcome: Outcome

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not 0 <= self.evidence.confidence <= 1:
            errors.append("evidence.confidence must be between 0 and 1")

        if not 0 <= self.signal.confidence <= 1:
            errors.append("signal.confidence must be between 0 and 1")

        if self.relationship.evidence_ref != self.evidence.source_ref:
            errors.append("relationship.evidence_ref must match evidence.source_ref")

        if self.signal.evidence_ref != self.evidence.source_ref:
            errors.append("signal.evidence_ref must match evidence.source_ref")

        if self.opportunity.signal_ref != self.signal.description:
            errors.append("opportunity.signal_ref must match signal.description")

        if self.outcome.opportunity_ref != self.opportunity.title:
            errors.append("outcome.opportunity_ref must match opportunity.title")

        return errors
