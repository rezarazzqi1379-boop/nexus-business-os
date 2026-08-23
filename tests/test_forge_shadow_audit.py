import json
from pathlib import Path

from nexus_control_plane.forge_shadow_audit import (
    ShadowAuditRecord,
    ShadowDisposition,
    validate_shadow_audit,
)


def _records():
    payload = json.loads(Path("data/forge_open_pr_shadow_audit_2026-08-23.json").read_text())
    return payload, [
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


def test_registered_shadow_snapshot_has_25_unique_evidence_backed_records():
    payload, records = _records()
    assert payload["status"] == "shadow_observation_not_merge_authority"
    assert len(records) == 25
    assert len({r.pr_number for r in records}) == 25
    assert validate_shadow_audit(records) == ()


def test_snapshot_records_multiple_non_promotional_dispositions():
    _, records = _records()
    dispositions = {r.disposition for r in records}
    assert ShadowDisposition.KEEP in dispositions
    assert ShadowDisposition.KEEP_SHADOW in dispositions
    assert ShadowDisposition.EXPERIMENT in dispositions
    assert ShadowDisposition.INCUBATOR in dispositions
    assert ShadowDisposition.EXTRACT in dispositions
    assert ShadowDisposition.HARDENING_HOLD in dispositions
    assert ShadowDisposition.HOLD in dispositions
    assert ShadowDisposition.INTEGRATION_ONLY in dispositions
    assert ShadowDisposition.SUPERSEDED in dispositions


def test_known_canonical_records_cannot_claim_wrong_owner():
    bad = ShadowAuditRecord(
        pr_number=999,
        disposition=ShadowDisposition.KEEP,
        evidence_ref="https://github.com/example/example/pull/999",
        rationale="adversarial owner mismatch",
        concern="evaluation",
        owner="PR999",
    )
    errors = validate_shadow_audit([bad])
    assert any("owner mismatch" in error for error in errors)


def test_unregistered_concern_cannot_claim_canonical_owner():
    bad = ShadowAuditRecord(
        pr_number=998,
        disposition=ShadowDisposition.HOLD,
        evidence_ref="https://github.com/example/example/pull/998",
        rationale="adversarial unregistered concern",
        concern="new_magic_framework",
        owner="PR998",
    )
    errors = validate_shadow_audit([bad])
    assert any("unregistered concern cannot claim owner" in error for error in errors)


def test_duplicate_pr_numbers_are_rejected():
    record = ShadowAuditRecord(
        pr_number=6,
        disposition=ShadowDisposition.KEEP,
        evidence_ref="https://github.com/example/example/pull/6",
        rationale="duplicate replay",
        concern="evaluation",
        owner="PR6",
    )
    errors = validate_shadow_audit([record, record])
    assert "duplicate pr_number:6" in errors
