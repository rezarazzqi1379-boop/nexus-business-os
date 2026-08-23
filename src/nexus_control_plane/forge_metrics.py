from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping

from nexus_control_plane.forge_registry import CANONICAL_OWNERS
from nexus_control_plane.forge_shadow_audit import ShadowAuditRecord, ShadowDisposition


@dataclass(frozen=True)
class ForgePortfolioMetrics:
    total_open_prs: int
    canonical_records: int
    canonical_registry_size: int
    canonical_coverage_ratio: float
    keep_like_count: int
    experimental_load: int
    superseded_load: int
    unresolved_load: int
    integration_only_load: int
    disposition_counts: Mapping[str, int]


def compute_forge_portfolio_metrics(records: Iterable[ShadowAuditRecord]) -> ForgePortfolioMetrics:
    rows = tuple(records)
    counts = Counter(r.disposition.value for r in rows)
    canonical_records = sum(1 for r in rows if r.concern and r.owner)
    registry_size = len(CANONICAL_OWNERS)
    represented = {
        r.concern
        for r in rows
        if r.concern and r.owner and CANONICAL_OWNERS.get(r.concern) == r.owner
    }
    keep_like = counts[ShadowDisposition.KEEP.value] + counts[ShadowDisposition.KEEP_SHADOW.value]
    experimental = (
        counts[ShadowDisposition.EXPERIMENT.value]
        + counts[ShadowDisposition.INCUBATOR.value]
        + counts[ShadowDisposition.EXTRACT.value]
    )
    superseded = counts[ShadowDisposition.SUPERSEDED.value]
    unresolved = (
        counts[ShadowDisposition.HOLD.value]
        + counts[ShadowDisposition.HARDENING_HOLD.value]
        + counts[ShadowDisposition.CHECKPOINT.value]
    )
    integration_only = counts[ShadowDisposition.INTEGRATION_ONLY.value]
    return ForgePortfolioMetrics(
        total_open_prs=len(rows),
        canonical_records=canonical_records,
        canonical_registry_size=registry_size,
        canonical_coverage_ratio=(len(represented) / registry_size if registry_size else 1.0),
        keep_like_count=keep_like,
        experimental_load=experimental,
        superseded_load=superseded,
        unresolved_load=unresolved,
        integration_only_load=integration_only,
        disposition_counts=dict(sorted(counts.items())),
    )


def portfolio_attention_flags(metrics: ForgePortfolioMetrics) -> tuple[str, ...]:
    flags: list[str] = []
    if metrics.canonical_coverage_ratio < 1.0:
        flags.append("canonical_registry_not_fully_represented_in_snapshot")
    if metrics.superseded_load:
        flags.append("superseded_open_prs_present")
    if metrics.experimental_load > metrics.keep_like_count:
        flags.append("experimental_load_exceeds_keep_like_load")
    if metrics.unresolved_load:
        flags.append("unresolved_or_hardening_hold_work_present")
    if metrics.integration_only_load:
        flags.append("integration_only_pr_should_not_accumulate_features")
    return tuple(flags)
