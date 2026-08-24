import json
from pathlib import Path

from nexus_verticals.business_genome import Decision
from nexus_verticals.business_genome_evaluation import (
    ShadowDecisionObservation,
    evaluate_shadow,
    promotion_evidence_gaps,
)


DATA_PATH = Path("data/business_genome_calibration_v0_1.json")


def _load_rows():
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    rows = []
    for item in payload["observations"]:
        rows.append(
            ShadowDecisionObservation(
                observation_id=item["observation_id"],
                project_id=item["project_id"],
                case_type=item["case_type"],
                recommendation=Decision(item["recommendation"]),
                human_decision=Decision(item["human_decision"]) if item["human_decision"] else None,
                outcome_success=item["outcome_success"],
                outcome_stage=item["outcome_stage"],
                safety_violation=item["safety_violation"],
                source_ref=item["source_ref"],
            )
        )
    return payload, rows


def test_real_calibration_dataset_is_traceable_and_valid():
    payload, rows = _load_rows()
    assert payload["dataset_id"] == "business-genome-calibration-v0.1"
    assert len(rows) == 5
    assert all(not row.validate() for row in rows)
    assert all("gmail:" in row.source_ref or "github:" in row.source_ref for row in rows)


def test_current_real_dataset_proves_human_alignment_but_not_business_roi():
    _, rows = _load_rows()
    report = evaluate_shadow(rows)
    assert report.total_observations == 5
    assert report.distinct_case_types == 5
    assert report.human_labeled == 5
    assert report.recommendation_human_agreement == 1.0
    assert report.outcome_labeled == 1
    assert report.stage_successes == 1
    assert report.final_outcome_labeled == 0
    assert report.pursue_outcome_precision is None
    assert report.pursue_false_positives == 0
    assert report.safety_violations == 0


def test_current_dataset_cannot_support_production_promotion():
    _, rows = _load_rows()
    gaps = promotion_evidence_gaps(evaluate_shadow(rows))
    assert gaps == ("insufficient_final_business_outcomes",)


def test_reply_stage_success_is_explicitly_not_final_commercial_success():
    payload, _ = _load_rows()
    route = next(
        item for item in payload["observations"]
        if item["observation_id"] == "cal-kcl-bpc-route-001"
    )
    assert route["outcome_success"] is True
    assert route["outcome_stage"] == "reply"
    assert "not an order/contract success" in route["evidence_note"]
