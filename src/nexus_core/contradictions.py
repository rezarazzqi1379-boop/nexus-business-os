from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AtomicClaim:
    claim_id: str
    subject_ref: str
    predicate: str
    value: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class Contradiction:
    subject_ref: str
    predicate: str
    claim_ids: tuple[str, str]
    values: tuple[str, str]


def detect_atomic_contradictions(claims: tuple[AtomicClaim, ...]) -> tuple[Contradiction, ...]:
    """Detect direct value conflicts without pretending semantic certainty.

    This deliberately catches only atomic same-subject/same-predicate conflicts.
    More complex semantic contradiction detection can be layered later as a
    hypothesis-producing model, but must not silently override source evidence.
    """
    groups: dict[tuple[str, str], list[AtomicClaim]] = {}
    for claim in claims:
        if not claim.claim_id.strip() or not claim.subject_ref.strip() or not claim.predicate.strip():
            raise ValueError("invalid_atomic_claim")
        if not claim.source_refs or len(claim.source_refs) != len(set(claim.source_refs)):
            raise ValueError("invalid_claim_provenance")
        groups.setdefault((claim.subject_ref, claim.predicate), []).append(claim)

    contradictions: list[Contradiction] = []
    for (subject_ref, predicate), grouped in sorted(groups.items()):
        ordered = sorted(grouped, key=lambda item: item.claim_id)
        for index, left in enumerate(ordered):
            for right in ordered[index + 1 :]:
                if left.value.strip().casefold() == right.value.strip().casefold():
                    continue
                contradictions.append(
                    Contradiction(
                        subject_ref=subject_ref,
                        predicate=predicate,
                        claim_ids=(left.claim_id, right.claim_id),
                        values=(left.value, right.value),
                    )
                )
    return tuple(contradictions)
