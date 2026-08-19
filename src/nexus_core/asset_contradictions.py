from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class AssetClaim:
    claim_id: str
    asset_id: str
    source_version_ref: str
    project_ref: str
    subject: str
    predicate: str
    value: str
    evidence_ref: str


@dataclass(frozen=True)
class AssetContradiction:
    left_claim_id: str
    right_claim_id: str
    project_ref: str
    subject: str
    predicate: str
    left_value: str
    right_value: str


def validate_claim(claim: AssetClaim) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(claim, AssetClaim):
        return ("claim_must_be_asset_claim",)
    for name, value in (
        ("claim_id", claim.claim_id),
        ("asset_id", claim.asset_id),
        ("source_version_ref", claim.source_version_ref),
        ("project_ref", claim.project_ref),
        ("subject", claim.subject),
        ("predicate", claim.predicate),
        ("value", claim.value),
        ("evidence_ref", claim.evidence_ref),
    ):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"invalid_{name}")
    return tuple(errors)


def detect_asset_contradictions(claims: Iterable[AssetClaim]) -> tuple[AssetContradiction, ...]:
    items = tuple(claims)
    seen_ids: set[str] = set()
    for claim in items:
        errors = validate_claim(claim)
        if errors:
            raise ValueError(",".join(errors))
        if claim.claim_id in seen_ids:
            raise ValueError("duplicate_claim_id")
        seen_ids.add(claim.claim_id)

    grouped: dict[tuple[str, str, str], list[AssetClaim]] = {}
    for claim in items:
        grouped.setdefault((claim.project_ref, claim.subject.casefold(), claim.predicate.casefold()), []).append(claim)

    contradictions: list[AssetContradiction] = []
    for (project_ref, subject_key, predicate_key), group in grouped.items():
        for i, left in enumerate(group):
            for right in group[i + 1:]:
                if left.value.strip().casefold() == right.value.strip().casefold():
                    continue
                if left.asset_id == right.asset_id and left.source_version_ref == right.source_version_ref:
                    continue
                contradictions.append(
                    AssetContradiction(
                        left_claim_id=left.claim_id,
                        right_claim_id=right.claim_id,
                        project_ref=project_ref,
                        subject=left.subject,
                        predicate=left.predicate,
                        left_value=left.value,
                        right_value=right.value,
                    )
                )
    contradictions.sort(key=lambda c: (c.project_ref, c.subject.casefold(), c.predicate.casefold(), c.left_claim_id, c.right_claim_id))
    return tuple(contradictions)
