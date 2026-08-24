import json
from pathlib import Path

from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import LiveEvidenceSignal, apply_live_evidence_signals
from nexus_brain.projection import project_projection
from nexus_brain.shadow_loop import ShadowTaskResult, apply_shadow_results, build_shadow_intents


SNAPSHOT = Path("data/operational/live_evidence_snapshot_2026-08-24.json")


def _graph_with_live_evidence():
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    signals = [LiveEvidenceSignal(**item) for item in payload["signals"]]
    return apply_live_evidence_signals(canonical_portfolio_graph(), signals)


def test_live_evidence_to_shadow_intents_is_deterministic_and_external_effect_free():
    graph = _graph_with_live_evidence()
    first = build_shadow_intents(graph)
    second = build_shadow_intents(graph)
    assert first == second
    assert {item.project_id for item in first} == {"PRJ-KCL-01", "PRJ-HYD-01"}
    assert all(item.external_effect is False for item in first)
    assert all(len(item.action_digest) == 64 for item in first)


def test_kcl_and_hydro_shadow_results_record_outcomes_without_clearing_blockers():
    graph = _graph_with_live_evidence()
    intents = build_shadow_intents(graph)
    results = [
        ShadowTaskResult(
            task_id=item.task_id,
            project_id=item.project_id,
            source_node_id=item.source_node_id,
            status="completed",
            summary="Shadow verification completed; findings require separate authority review.",
            evidence_refs=(f"shadow-run:{item.task_id}",),
        )
        for item in intents
    ]
    apply_shadow_results(graph, results)

    kcl = project_projection(graph, "PRJ-KCL-01")
    hyd = project_projection(graph, "PRJ-HYD-01")
    assert kcl["consequential_use_allowed"] is False
    assert hyd["consequential_use_allowed"] is False
    assert "blocking_unknown" in kcl["blockers"]
    assert "blocking_unknown" in hyd["blockers"]

    outcomes = [n for n in graph.nodes.values() if n.type.value == "outcome"]
    assert len(outcomes) == len(intents)
    assert all(n.authority_tier.value == "operational_state" for n in outcomes)
    assert all(n.attributes["external_effect"] is False for n in outcomes)


def test_duplicate_shadow_result_fails_closed():
    graph = _graph_with_live_evidence()
    item = build_shadow_intents(graph)[0]
    result = ShadowTaskResult(
        task_id=item.task_id,
        project_id=item.project_id,
        source_node_id=item.source_node_id,
        status="completed",
        summary="done",
        evidence_refs=(f"shadow-run:{item.task_id}",),
    )
    apply_shadow_results(graph, [result])
    try:
        apply_shadow_results(graph, [result])
    except ValueError as exc:
        assert "duplicate shadow result" in str(exc)
    else:
        raise AssertionError("duplicate shadow result must fail closed")


def test_shadow_result_without_provenance_fails_closed():
    graph = _graph_with_live_evidence()
    item = build_shadow_intents(graph)[0]
    result = ShadowTaskResult(
        task_id=item.task_id,
        project_id=item.project_id,
        source_node_id=item.source_node_id,
        status="completed",
        summary="unproven result",
    )
    try:
        apply_shadow_results(graph, [result])
    except ValueError as exc:
        assert "fact requires provenance" in str(exc)
    else:
        raise AssertionError("shadow result without provenance must fail closed")


def test_shadow_result_cannot_reference_unknown_project_or_source():
    graph = _graph_with_live_evidence()
    bad = ShadowTaskResult(
        task_id="shadow:bad",
        project_id="PRJ-NOT-REAL",
        source_node_id="MISSING",
        status="completed",
        summary="bad",
    )
    try:
        apply_shadow_results(graph, [bad])
    except ValueError as exc:
        assert "unknown project" in str(exc)
    else:
        raise AssertionError("unknown project must fail closed")
