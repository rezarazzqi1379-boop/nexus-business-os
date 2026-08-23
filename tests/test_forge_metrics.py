import json
from pathlib import Path

from nexus_control_plane.forge_metrics import (
    compute_forge_portfolio_metrics,
    portfolio_attention_flags,
)
from nexus_control_plane.forge_shadow_audit import ShadowAuditRecord, ShadowDisposition


def _records():
    payload = json.loads(Path("data/forge_open_pr_shadow_audit_2026-08-23.json").read_text())
    return [
        ShadowAuditRecord(
            pr_number=row["pr_number"],
            disposition=ShadowDisposition(row["disposition"]),
            evidence_ref=row["evidence_ref"],
            rationale=row["rationale"],
            concern=row.get("concern"),
            owner=row.get("owner"),
        )
        for row in payload["records"]
    ]


def test_current_portfolio_metrics_are_reproducible_from_snapshot():
    metrics = compute_forge_portfolio_metrics(_records())
    assert metrics.total_open_prs == 27
    assert metrics.canonical_records == 16
    assert metrics.canonical_registry_size == 16
    assert metrics.canonical_coverage_ratio == 1.0
    assert metrics.keep_like_count == 14
    assert metrics.experimental_load == 6
    assert metrics.superseded_load == 3
    assert metrics.unresolved_load == 3
    assert metrics.integration_only_load == 1


def test_current_portfolio_attention_flags_preserve_cleanup_pressure():
    flags = portfolio_attention_flags(compute_forge_portfolio_metrics(_records()))
    assert "canonical_registry_not_fully_represented_in_snapshot" not in flags
    assert "superseded_open_prs_present" in flags
    assert "unresolved_or_hardening_hold_work_present" in flags
    assert "integration_only_pr_should_not_accumulate_features" in flags
    assert "experimental_load_exceeds_keep_like_load" not in flags


def test_missing_canonical_owner_is_detected_as_snapshot_coverage_gap():
    rows = [r for r in _records() if r.concern != "evidence_semantics"]
    metrics = compute_forge_portfolio_metrics(rows)
    assert metrics.canonical_coverage_ratio < 1.0
    assert "canonical_registry_not_fully_represented_in_snapshot" in portfolio_attention_flags(metrics)
