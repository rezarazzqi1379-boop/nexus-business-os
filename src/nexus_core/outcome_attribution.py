from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Contribution:
    contributor_id: str
    contributor_type: str
    outcome_id: str
    directness: str
    evidence_refs: tuple[str, ...]
    confidence: float
    observed_effect: float


@dataclass(frozen=True)
class AttributionSummary:
    contributor_id: str
    contributor_type: str
    weighted_effect: float
    evidence_count: int
    confidence_band: str


_ALLOWED_DIRECTNESS = {"direct", "supporting", "contextual"}
_ALLOWED_TYPES = {
    "source",
    "person",
    "company",
    "intermediary",
    "message",
    "experiment",
    "paper",
    "tool",
    "code_change",
    "network_path",
}
_DIRECTNESS_WEIGHT = {"direct": 1.0, "supporting": 0.6, "contextual": 0.25}


def validate_contribution(item: Contribution) -> tuple[str, ...]:
    errors: list[str] = []
    if not item.contributor_id.strip():
        errors.append("missing_contributor_id")
    if item.contributor_type not in _ALLOWED_TYPES:
        errors.append("invalid_contributor_type")
    if not item.outcome_id.strip():
        errors.append("missing_outcome_id")
    if item.directness not in _ALLOWED_DIRECTNESS:
        errors.append("invalid_directness")
    if not item.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in item.evidence_refs):
        errors.append("missing_evidence_refs")
    if len(item.evidence_refs) != len(set(item.evidence_refs)):
        errors.append("duplicate_evidence_refs")
    if not 0.0 <= item.confidence <= 1.0:
        errors.append("invalid_confidence")
    if item.observed_effect < -1.0 or item.observed_effect > 1.0:
        errors.append("invalid_observed_effect")
    return tuple(errors)


def summarize_attribution(items: Iterable[Contribution]) -> tuple[AttributionSummary, ...]:
    """Summarize evidence-linked contribution without claiming causal proof.

    This is attribution bookkeeping, not causal inference. A contributor receives
    credit only from explicit outcome-linked evidence. Contextual and low-confidence
    contributions are intentionally discounted.
    """
    grouped: dict[tuple[str, str], list[Contribution]] = {}
    seen_identity: set[tuple[str, str, str, str]] = set()
    for item in items:
        errors = validate_contribution(item)
        if errors:
            raise ValueError(",".join(errors))
        identity = (item.contributor_id, item.contributor_type, item.outcome_id, item.directness)
        if identity in seen_identity:
            raise ValueError("duplicate_contribution_identity")
        seen_identity.add(identity)
        grouped.setdefault((item.contributor_id, item.contributor_type), []).append(item)

    summaries: list[AttributionSummary] = []
    for (contributor_id, contributor_type), values in grouped.items():
        weighted = sum(v.observed_effect * v.confidence * _DIRECTNESS_WEIGHT[v.directness] for v in values)
        evidence_count = len({ref for v in values for ref in v.evidence_refs})
        avg_confidence = sum(v.confidence for v in values) / len(values)
        if len(values) >= 5 and avg_confidence >= 0.75:
            band = "usable"
        elif len(values) >= 2 and avg_confidence >= 0.5:
            band = "emerging"
        else:
            band = "insufficient"
        summaries.append(
            AttributionSummary(
                contributor_id=contributor_id,
                contributor_type=contributor_type,
                weighted_effect=round(weighted, 6),
                evidence_count=evidence_count,
                confidence_band=band,
            )
        )

    return tuple(sorted(summaries, key=lambda x: (-x.weighted_effect, x.contributor_type, x.contributor_id)))
