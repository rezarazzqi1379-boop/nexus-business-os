import json
from pathlib import Path


def test_persisted_generation_snapshot_is_shadow_and_evidence_backed():
    path = Path("data/forge_generation_ledger_v0_1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "forge_generation_ledger_v0_1"
    assert payload["authority"] == "shadow_observation_not_merge_or_production_authority"
    assert len(payload["entries"]) == 1
    entry = payload["entries"][0]
    assert entry["generation_id"] == "forge-gen-2026-08-23-evidence-loop-01"
    assert entry["technical_verification"]["pytest_passed"] == 184
    assert entry["technical_verification"]["pytest_failed"] == 0
    assert entry["evidence_refs"]
    assert entry["promotion_authorized"] is False
    assert entry["independent_audit_passed"] is False
    assert entry["terminal_business_outcome_observed"] is False
