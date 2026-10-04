import json
from pathlib import Path


def _contract():
    path = Path(__file__).parents[1] / "docs" / "replays" / "measurement_contract_v0_1.json"
    return json.loads(path.read_text())


def test_measurement_contract_requires_five_comparable_runs():
    contract = _contract()
    assert contract["minimum_comparable_runs_before_promotion"] >= 5
    assert contract["promotion_rules"]["requires_at_least_five_comparable_runs"] is True


def test_measurement_contract_cannot_promote_without_human_review_and_evidence():
    rules = _contract()["promotion_rules"]
    assert rules["requires_human_review"] is True
    assert rules["requires_evidence_links"] is True
    assert rules["requires_no_safety_regression"] is True


def test_roi_claim_requires_real_commercial_outcomes():
    assert _contract()["promotion_rules"]["roi_claim_requires_actual_commercial_outcomes"] is True


def test_contract_tracks_failure_and_correction_signals():
    required = set(_contract()["required_fields"])
    assert {
        "duplicate_block_count",
        "unsupported_claim_block_count",
        "authority_gap_count",
        "clarification_count",
        "rework_count",
        "human_correction_count",
        "evidence_links",
    } <= required
