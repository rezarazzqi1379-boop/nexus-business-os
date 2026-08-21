from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from .research_data_mesh import ResearchHit, fuse_hits

EvidenceAuthority = Literal[
    "buyer_end_user",
    "approved_internal",
    "verified_project",
    "supplier_oem",
    "inference",
    "historical_other_project",
    "unknown",
]
Resolution = Literal["support", "refute", "unresolved"]

_AUTHORITY_WEIGHT: dict[str, int] = {
    "buyer_end_user": 7,
    "approved_internal": 6,
    "verified_project": 5,
    "supplier_oem": 4,
    "inference": 3,
    "historical_other_project": 2,
    "unknown": 1,
}


@dataclass(frozen=True)
class AuthorityTaggedHit:
    hit: ResearchHit
    authority: EvidenceAuthority


@dataclass(frozen=True)
class AuthorityResolution:
    canonical_key: str
    contradiction: bool
    resolution: Resolution
    support_authority: int
    refute_authority: int
    decisive_source_ids: tuple[str, ...]
    requires_human_review: bool


def _validate_tagged(item: object) -> AuthorityTaggedHit:
    if not isinstance(item, AuthorityTaggedHit) or not isinstance(item.hit, ResearchHit):
        raise ValueError("invalid_authority_hit")
    if item.authority not in _AUTHORITY_WEIGHT:
        raise ValueError("invalid_authority")
    return item


def resolve_authority_contradiction(items: Iterable[AuthorityTaggedHit]) -> AuthorityResolution:
    """Resolve which stance has higher operational authority without hiding contradiction.

    This function does not declare a claim true. It only determines whether one side of an
    explicit contradiction has a strictly higher authority tier under the NEXUS hierarchy.
    Equal top authority remains unresolved and requires review.
    """
    try:
        tagged = tuple(_validate_tagged(item) for item in items)
    except TypeError as exc:
        raise ValueError("authority_hits_must_be_iterable") from exc
    if not tagged:
        raise ValueError("authority_resolution_requires_hits")

    hits = tuple(item.hit for item in tagged)
    fused = fuse_hits(hits)
    if len(fused) != 1:
        raise ValueError("authority_resolution_requires_one_claim")
    finding = fused[0]

    support = [item for item in tagged if item.hit.stance == "support"]
    refute = [item for item in tagged if item.hit.stance == "refute"]
    support_authority = max((_AUTHORITY_WEIGHT[item.authority] for item in support), default=0)
    refute_authority = max((_AUTHORITY_WEIGHT[item.authority] for item in refute), default=0)

    if not finding.contradiction:
        if support and not refute:
            resolution: Resolution = "support"
            decisive = tuple(sorted(item.hit.source_id for item in support if _AUTHORITY_WEIGHT[item.authority] == support_authority))
        elif refute and not support:
            resolution = "refute"
            decisive = tuple(sorted(item.hit.source_id for item in refute if _AUTHORITY_WEIGHT[item.authority] == refute_authority))
        else:
            resolution = "unresolved"
            decisive = ()
        return AuthorityResolution(
            canonical_key=finding.canonical_key,
            contradiction=False,
            resolution=resolution,
            support_authority=support_authority,
            refute_authority=refute_authority,
            decisive_source_ids=decisive,
            requires_human_review=False,
        )

    if support_authority > refute_authority:
        resolution = "support"
        decisive = tuple(sorted(item.hit.source_id for item in support if _AUTHORITY_WEIGHT[item.authority] == support_authority))
        review = False
    elif refute_authority > support_authority:
        resolution = "refute"
        decisive = tuple(sorted(item.hit.source_id for item in refute if _AUTHORITY_WEIGHT[item.authority] == refute_authority))
        review = False
    else:
        resolution = "unresolved"
        decisive = tuple(sorted(item.hit.source_id for item in tagged if item.hit.stance in {"support", "refute"} and _AUTHORITY_WEIGHT[item.authority] == support_authority))
        review = True

    return AuthorityResolution(
        canonical_key=finding.canonical_key,
        contradiction=True,
        resolution=resolution,
        support_authority=support_authority,
        refute_authority=refute_authority,
        decisive_source_ids=decisive,
        requires_human_review=review,
    )
