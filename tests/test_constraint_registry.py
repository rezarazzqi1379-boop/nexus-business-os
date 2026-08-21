import pytest

from nexus_core.constraint_registry import (
    Constraint,
    Decision,
    audit_constraints,
    evaluate_constraint,
)


def make_constraint(**overrides):
    raw = {
        "constraint_id": "example",
        "title": "Example limitation",
        "kind": "capability",
        "evidence": "Observed in a reproducible run.",
        "value_blocked": 5,
        "recurrence": 4,
        "existing_option_score": 0,
        "build_cost": 2,
        "maintenance_cost": 1,
        "risk": 1,
        "owner": "engineering",
        "success_metric": "Acceptance test passes.",
        "rollback": "Disable the feature.",
        "status": "observed",
    }
    raw.update(overrides)
    return Constraint.from_dict(raw)


def test_human_gate_is_never_routed_to_a_bypass():
    result = evaluate_constraint(make_constraint(kind="human_gate"))
    assert result.decision == Decision.RESPECT_BOUNDARY
    assert result.requires_human_gate is True


def test_supported_existing_option_wins_over_new_code():
    result = evaluate_constraint(make_constraint(existing_option_score=5))
    assert result.decision == Decision.USE_EXISTING


def test_high_value_data_gap_routes_to_narrow_adapter():
    result = evaluate_constraint(make_constraint(kind="data"))
    assert result.decision == Decision.BUILD_ADAPTER


def test_low_value_build_is_deferred():
    result = evaluate_constraint(
        make_constraint(
            value_blocked=1,
            recurrence=1,
            build_cost=4,
            maintenance_cost=3,
            risk=3,
        )
    )
    assert result.decision == Decision.DEFER


def test_boolean_and_out_of_range_scores_fail_closed():
    with pytest.raises(ValueError, match="invalid_risk"):
        make_constraint(risk=True)
    with pytest.raises(ValueError, match="invalid_risk"):
        make_constraint(risk=7)


def test_duplicate_ids_and_unbounded_batches_fail_closed():
    record = {
        "constraint_id": "duplicate",
        "title": "Example",
        "kind": "quota",
        "evidence": "Measured plan cap.",
        "value_blocked": 2,
        "recurrence": 3,
        "existing_option_score": 3,
        "build_cost": 2,
        "maintenance_cost": 1,
        "risk": 1,
        "owner": "operations",
        "success_metric": "Workflow completes.",
        "rollback": "Restore prior configuration.",
    }
    with pytest.raises(ValueError, match="duplicate_constraint_id"):
        audit_constraints([record, record])
    with pytest.raises(ValueError, match="invalid_constraint_batch"):
        audit_constraints([record] * 1_001)
