from nexus_control_plane.memory_intervention import (
    MemoryIntervention,
    MemoryInterventionRequest,
    evaluate_memory_intervention,
)
from nexus_control_plane.reliability_probe import ReliabilityRun, summarize_reliability


def test_dynamic_stale_memory_requires_verification_before_reuse():
    decision = evaluate_memory_intervention(MemoryInterventionRequest(
        concern="cross_project_runtime",
        project_id="KCL",
        applicability_match=True,
        memory_fresh=False,
        dynamic_state=True,
        consequential=False,
    ))
    assert decision.intervention is MemoryIntervention.VERIFY_FIRST
    assert decision.action_authorized is False
    assert "refresh_dynamic_state" in decision.required_checks


def test_binding_shift_requires_rebinding_not_full_trajectory_injection():
    decision = evaluate_memory_intervention(MemoryInterventionRequest(
        concern="business_genome",
        project_id="HYDROTESTER",
        applicability_match=True,
        memory_fresh=True,
        dynamic_state=False,
        consequential=True,
        trajectory_binding_changed=True,
    ))
    assert decision.intervention is MemoryIntervention.VERIFY_FIRST
    assert "rebind_current_entities" in decision.required_checks
    assert decision.action_authorized is False


def test_irrelevant_memory_stays_silent():
    decision = evaluate_memory_intervention(MemoryInterventionRequest(
        concern="business_genome",
        project_id="CAN_FORMING",
        applicability_match=False,
        memory_fresh=True,
        dynamic_state=False,
        consequential=False,
    ))
    assert decision.intervention is MemoryIntervention.SILENT
    assert decision.action_authorized is False


def test_reliability_separates_clean_execution_from_semantic_correctness():
    snapshot = summarize_reliability((
        ReliabilityRun("r1", True, 100, 2, 20, True),
        ReliabilityRun("r2", True, 120, 2, 21, False),
        ReliabilityRun("r3", True, 150, 3, 22, True),
    ))
    assert snapshot.success_rate == 1.0
    assert snapshot.semantic_success_rate == 2 / 3
    assert snapshot.all_runs_success is False
    assert snapshot.p50_latency_ms == 120
    assert snapshot.p95_latency_ms == 150
    assert snapshot.min_tool_calls == 2
    assert snapshot.max_tool_calls == 3


def test_reliability_requires_unique_runs():
    try:
        summarize_reliability((
            ReliabilityRun("same", True, 10, 1, 1, True),
            ReliabilityRun("same", True, 11, 1, 1, True),
        ))
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate run ids must fail closed")
