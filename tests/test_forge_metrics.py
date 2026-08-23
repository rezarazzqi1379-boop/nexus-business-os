import json
from pathlib import Path

from nexus_control_plane.forge_metrics import (
    compute_forge_portfolio_metrics,
    portfolio_attention_flags,
)
from nexus_control_plane.forge_shadow_audit import ShadowAuditRecord, ShadowDisposition


def _payload_and_records():
    payload = json.loads(Path("data/forge_open_pr_shadow_audit_2026-08-23.json").read_text())
    records = [
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
    return payload, records


def test_current_portfolio_metrics_are_reproducible_from_snapshot():
    payload, records = _payload_and_records()
    metrics = compute_forge_portfolio_metrics(records)
    assert metrics.total_open_prs == 27
    assert metrics.canonical_records == 16
    assert metrics.canonical_registry_size == 16
    assert metrics.canonical_coverage_ratio == 1.0
    assert metrics.keep_like_count == 14
    assert metrics.experimental_load == 6
    assert metrics.superseded_load == 3
    assert metrics.unresolved_load == 3
    assert metrics.integration_only_load == 1
    assert payload["metrics"]["canonical_registry_coverage"] == "16/16"
    assert payload["metrics"]["keep_like"] == metrics.keep_like_count
    assert payload["metrics"]["experimental_incubator_extract"] == metrics.experimental_load
    assert payload["metrics"]["superseded_open"] == metrics.superseded_load
    assert payload["metrics"]["unresolved_hold_checkpoint"] == metrics.unresolved_load
    assert payload["metrics"]["integration_only"] == metrics.integration_only_load


def test_current_portfolio_attention_flags_preserve_cleanup_pressure():
    payload, records = _payload_and_records()
    flags = portfolio_attention_flags(compute_forge_portfolio_metrics(records))
    assert "canonical_registry_not_fully_represented_in_snapshot" not in flags
    assert "superseded_open_prs_present" in flags
    assert "unresolved_or_hardening_hold_work_present" in flags
    assert "integration_only_pr_should_not_accumulate_features" in flags
    assert "experimental_load_exceeds_keep_like_load" not in flags
    assert payload["metrics"]["attention_flags"] == list(flags)


def test_missing_canonical_owner_is_detected_as_snapshot_coverage_gap():
    _, records = _payload_and_records()
    rows = [r for r in records if r.concern != "evidence_semantics"]
    metrics = compute_forge_portfolio_metrics(rows)
    assert metrics.canonical_coverage_ratio < 1.0
    assert "canonical_registry_not_fully_represented_in_snapshot" in portfolio_attention_flags(metrics)
