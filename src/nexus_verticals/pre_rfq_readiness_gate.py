"""Bounded candidate pre-RFQ readiness gate for shadow evaluation only.

The gate classifies unresolved inputs before supplier outreach. It never sends,
blocks production, or changes permissions. A HOLD here means 'collect/confirm the
critical input before using this candidate workflow for outreach'.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ReadinessDimension(str, Enum):
    TECHNICAL_BOUNDARY = "technical_boundary"
    SCOPE_BOUNDARY = "scope_boundary"
    REGULATORY_COMMERCIAL = "regulatory_commercial"
    OTHER = "other"


@dataclass(frozen=True)
class ReadinessUnknown:
    key: str
    dimension: ReadinessDimension
    decision_critical: bool
    evidence_ref: str

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.evidence_ref.strip():
            raise ValueError("unknown key and evidence_ref are required")


@dataclass(frozen=True)
class ReadinessAssessment:
    ready_for_outreach: bool
    blocking_keys: tuple[str, ...]
    disclosed_noncritical_keys: tuple[str, ...]
    reason: str


def assess_pre_rfq_readiness(unknowns: Iterable[ReadinessUnknown]) -> ReadinessAssessment:
    rows = tuple(unknowns)
    if any(not isinstance(row, ReadinessUnknown) for row in rows):
        raise ValueError("unknowns must contain ReadinessUnknown objects")

    blockers = sorted({row.key.strip() for row in rows if row.decision_critical})
    noncritical = sorted({row.key.strip() for row in rows if not row.decision_critical})
    if blockers:
        return ReadinessAssessment(
            ready_for_outreach=False,
            blocking_keys=tuple(blockers),
            disclosed_noncritical_keys=tuple(noncritical),
            reason="decision-critical pre-RFQ unknowns require confirmation before candidate outreach",
        )
    return ReadinessAssessment(
        ready_for_outreach=True,
        blocking_keys=(),
        disclosed_noncritical_keys=tuple(noncritical),
        reason="no decision-critical pre-RFQ unknowns recorded; non-critical unknowns remain disclosed",
    )
