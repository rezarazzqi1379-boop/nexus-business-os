"""Deterministic learning bridge for Business Genome shadow observations.

This module converts validated calibration observations into append-only outcome
ledger entries and bounded negative-knowledge events. It does not mutate scoring
weights, contact suppliers, or authorize production changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .business_genome import Decision
from .business_genome_evaluation import ShadowDecisionObservation


class OutcomeKind(str, Enum):
    ALIGNMENT = "alignment"
    STAGE_SUCCESS = "stage_success"
    FINAL_SUCCESS = "final_success"
    FALSE_POSITIVE = "false_positive"
    SAFETY_FAILURE = "safety_failure"
    OPEN = "open"


@dataclass(frozen=True)
class OutcomeLedgerEntry:
    ledger_id: str
    observation_id: str
    project_id: str
    recommendation: Decision
    human_decision: Decision | None
    outcome_kind: OutcomeKind
    outcome_stage: str | None
    source_ref: str


@dataclass(frozen=True)
class NegativeKnowledgeEvent:
    event_id: str
    observation_id: str
    project_id: str
    category: str
    reason: str
    source_ref: str


def classify_outcome(row: ShadowDecisionObservation) -> OutcomeKind:
    if row.validate():
        raise ValueError("invalid shadow observation")
    if row.safety_violation:
        return OutcomeKind.SAFETY_FAILURE
    if row.outcome_success is True:
        if row.outcome_stage in {"contract", "order"}:
            return OutcomeKind.FINAL_SUCCESS
        return OutcomeKind.STAGE_SUCCESS
    if row.outcome_success is False:
        if row.recommendation == Decision.PURSUE:
            return OutcomeKind.FALSE_POSITIVE
        return OutcomeKind.OPEN
    if row.human_decision is not None and row.human_decision == row.recommendation:
        return OutcomeKind.ALIGNMENT
    return OutcomeKind.OPEN


def to_ledger_entry(row: ShadowDecisionObservation) -> OutcomeLedgerEntry:
    kind = classify_outcome(row)
    return OutcomeLedgerEntry(
        ledger_id=f"ledger:{row.observation_id}",
        observation_id=row.observation_id,
        project_id=row.project_id,
        recommendation=row.recommendation,
        human_decision=row.human_decision,
        outcome_kind=kind,
        outcome_stage=row.outcome_stage,
        source_ref=row.source_ref,
    )


def to_negative_knowledge(row: ShadowDecisionObservation) -> NegativeKnowledgeEvent | None:
    kind = classify_outcome(row)
    if kind == OutcomeKind.SAFETY_FAILURE:
        return NegativeKnowledgeEvent(
            event_id=f"negative:{row.observation_id}:safety",
            observation_id=row.observation_id,
            project_id=row.project_id,
            category="safety_failure",
            reason="observed safety violation; do not promote equivalent behavior without new evidence and approval",
            source_ref=row.source_ref,
        )
    if kind == OutcomeKind.FALSE_POSITIVE:
        return NegativeKnowledgeEvent(
            event_id=f"negative:{row.observation_id}:false-positive",
            observation_id=row.observation_id,
            project_id=row.project_id,
            category="pursue_false_positive",
            reason="PURSUE recommendation had an observed unsuccessful outcome at the recorded stage",
            source_ref=row.source_ref,
        )
    return None


def build_learning_batch(observations: Iterable[ShadowDecisionObservation]) -> tuple[tuple[OutcomeLedgerEntry, ...], tuple[NegativeKnowledgeEvent, ...]]:
    """Build deterministic, deduplicated append candidates from observations."""
    valid: dict[str, ShadowDecisionObservation] = {}
    for row in observations:
        if row.validate():
            continue
        existing = valid.get(row.observation_id)
        if existing is not None and existing != row:
            raise ValueError(f"conflicting duplicate observation_id: {row.observation_id}")
        valid[row.observation_id] = row

    ordered = [valid[key] for key in sorted(valid)]
    ledger = tuple(to_ledger_entry(row) for row in ordered)
    negative = tuple(event for row in ordered if (event := to_negative_knowledge(row)) is not None)
    return ledger, negative
