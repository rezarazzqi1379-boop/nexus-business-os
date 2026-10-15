import json
from pathlib import Path

from nexus_core.vertical_acceptance import (
    TraceEnvelope,
    VerticalAcceptancePolicy,
    VerticalRunObservation,
    assess_vertical_runs,
)


def test_first_hydrotester_prospective_replay_is_not_scoreable_until_measurements_exist():
    path = Path(__file__).resolve().parents[1] / "data" / "research" / "hydrotester_prospective_replay_run_001.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload["observed_metrics"]

    run = VerticalRunObservation(
        trace=TraceEnvelope(
            workflow_name=payload["workflow_name"],
            project_id=payload["project_id"],
            candidate_id=payload["candidate_id"],
            run_id=payload["run_id"],
            data_classification=payload["data_classification"],
        ),
        decisions=metrics["decisions"],
        human_corrections=metrics["human_corrections"],
        unknowns_presented=metrics["unknowns_presented"],
        unknowns_blocked=metrics["unknowns_blocked"],
        duplicate_attempts=metrics["duplicate_attempts"],
        duplicates_prevented=metrics["duplicates_prevented"],
        decision_time_ms=metrics["decision_time_ms"],
        policy_violations=metrics["policy_violations"],
        cross_project_leaks=metrics["cross_project_leaks"],
        external_effects=metrics["external_effects"],
    )
    policy = VerticalAcceptancePolicy(
        min_runs=1,
        max_correction_rate=0.10,
        min_unknown_block_rate=1.0,
        min_duplicate_prevention_rate=1.0,
        max_mean_decision_time_ms=1500,
    )

    result = assess_vertical_runs(payload["project_id"], payload["candidate_id"], [run], policy)

    assert result.verdict == "FAIL"
    assert result.run_count == 1
    assert result.correction_rate is None
    assert result.unknown_block_rate == 1.0
    assert result.duplicate_prevention_rate is None
    assert result.mean_decision_time_ms is None
    assert any("human correction" in reason for reason in result.reasons)
    assert any("duplicate prevention is unmeasured" in reason for reason in result.reasons)
    assert any("decision time" in reason for reason in result.reasons)
    assert payload["expected_acceptance_state"] == "FAIL_NOT_SCOREABLE"
    assert payload["authority_effect"] == "NONE"
    assert payload["external_effect"] == "NONE"
