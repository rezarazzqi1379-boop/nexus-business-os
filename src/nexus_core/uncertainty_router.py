from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class UncertaintyKind(str, Enum):
    EVIDENCE_GAP = "evidence_gap"
    CONFLICT = "conflict"
    LOW_CONFIDENCE = "low_confidence"
    NONE = "none"


class NextAction(str, Enum):
    COLLECT_EVIDENCE = "collect_evidence"
    RESOLVE_CONFLICT = "resolve_conflict"
    RUN_EXPERIMENT = "run_experiment"
    PROMOTE = "promote"


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    value: str
    confidence: float
    source_ref: str


@dataclass(frozen=True)
class UncertaintyDecision:
    kind: UncertaintyKind
    next_action: NextAction
    rationale: tuple[str, ...]


def classify_uncertainty(
    evidence: Iterable[EvidenceItem],
    *,
    min_items: int = 2,
    promotion_confidence: float = 0.8,
) -> UncertaintyDecision:
    """Distinguish missing evidence from conflicting evidence.

    Research on evidence-based active learning shows that uncertainty caused by
    insufficient evidence should not be treated the same as uncertainty caused by
    strong but conflicting evidence. NEXUS uses that distinction to choose whether
    to gather more data or run a contradiction-resolution experiment.
    """
    items = tuple(evidence)
    if not items:
        return UncertaintyDecision(
            UncertaintyKind.EVIDENCE_GAP,
            NextAction.COLLECT_EVIDENCE,
            ("no_evidence",),
        )

    if any(not item.evidence_id.strip() or not item.source_ref.strip() for item in items):
        return UncertaintyDecision(
            UncertaintyKind.EVIDENCE_GAP,
            NextAction.COLLECT_EVIDENCE,
            ("invalid_provenance",),
        )

    if any(not 0.0 <= item.confidence <= 1.0 for item in items):
        return UncertaintyDecision(
            UncertaintyKind.EVIDENCE_GAP,
            NextAction.COLLECT_EVIDENCE,
            ("invalid_confidence",),
        )

    values = {item.value.strip().casefold() for item in items if item.value.strip()}
    if len(values) > 1:
        strong_values = {
            item.value.strip().casefold()
            for item in items
            if item.value.strip() and item.confidence >= promotion_confidence
        }
        if len(strong_values) > 1:
            return UncertaintyDecision(
                UncertaintyKind.CONFLICT,
                NextAction.RESOLVE_CONFLICT,
                ("strong_conflicting_evidence",),
            )
        return UncertaintyDecision(
            UncertaintyKind.LOW_CONFIDENCE,
            NextAction.RUN_EXPERIMENT,
            ("mixed_values_without_strong_conflict",),
        )

    if len(items) < min_items:
        return UncertaintyDecision(
            UncertaintyKind.EVIDENCE_GAP,
            NextAction.COLLECT_EVIDENCE,
            ("insufficient_independent_evidence",),
        )

    if max(item.confidence for item in items) < promotion_confidence:
        return UncertaintyDecision(
            UncertaintyKind.LOW_CONFIDENCE,
            NextAction.RUN_EXPERIMENT,
            ("evidence_present_but_low_confidence",),
        )

    return UncertaintyDecision(UncertaintyKind.NONE, NextAction.PROMOTE, ())
