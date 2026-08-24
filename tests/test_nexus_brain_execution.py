from dataclasses import replace

from nexus_brain.command import recommend_internal_actions
from nexus_brain.execution import (
    build_read_only_execution_intent,
    canonical_project_snapshot_digest,
    validate_execution_intent_binding,
)
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live_snapshot import load_live_snapshot


CREATED = "2026-08-24T08:50:00Z"


def live_graph():
    graph, _ = load_live_snapshot("data/operational/live_evidence_snapshot_2026-08-24.json")
    return graph


def action_for(graph, source_id):
    return next(a for a in recommend_internal_actions(graph) if a.source_node_id == source_id)


def test_build_execution_intent_binds_project_source_snapshot_and_payload():
    graph = live_graph()
    rec = action_for(graph, "LIVE-HYD-GH-REV12-ACK-20260823")
    intent = build_read_only_execution_intent(
        graph,
        rec,
        created_at=CREATED,
        payload={"mode": "normalize_against_rev_1_2", "read_only": True},
    )
    assert intent.intent_id.startswith("EI-")
    assert intent.project_id == "PRJ-HYD-01"
    assert intent.source_refs == ("gmail:1a02f17fe9dd0b73",)
    assert intent.external_execution_allowed is False
    assert intent.consequential is False
    assert intent.canonical_snapshot_digest == canonical_project_snapshot_digest(graph, "PRJ-HYD-01")
    assert validate_execution_intent_binding(graph, intent) is True


def test_same_inputs_produce_same_intent_id():
    graph = live_graph()
    rec = action_for(graph, "LIVE-KCL-OMS-PERMIT-20260824")
    kwargs = {"created_at": CREATED, "payload": {"check": "permit_authority"}}
    first = build_read_only_execution_intent(graph, rec, **kwargs)
    second = build_read_only_execution_intent(graph, rec, **kwargs)
    assert first.intent_id == second.intent_id


def test_payload_change_invalidates_prior_intent():
    graph = live_graph()
    rec = action_for(graph, "LIVE-KCL-OMS-PERMIT-20260824")
    intent = build_read_only_execution_intent(graph, rec, created_at=CREATED, payload={"a": 1})
    changed = replace(intent, payload={"a": 2})
    assert validate_execution_intent_binding(graph, changed) is False


def test_snapshot_change_invalidates_prior_intent():
    graph = live_graph()
    rec = action_for(graph, "LIVE-HYD-GH-REV12-ACK-20260823")
    intent = build_read_only_execution_intent(graph, rec, created_at=CREATED)
    graph.nodes["HYD-PMAX"].attributes["review_probe"] = "changed"
    assert validate_execution_intent_binding(graph, intent) is False


def test_cross_project_source_mismatch_fails_closed():
    graph = live_graph()
    rec = action_for(graph, "LIVE-HYD-GH-REV12-ACK-20260823")
    bad = replace(rec, project_id="PRJ-KCL-01")
    try:
        build_read_only_execution_intent(graph, bad, created_at=CREATED)
    except ValueError as exc:
        assert "project mismatch" in str(exc)
    else:
        raise AssertionError("cross-project source binding accepted")


def test_external_or_consequential_intent_is_never_accepted_by_v0_1():
    graph = live_graph()
    rec = action_for(graph, "LIVE-KCL-OMS-PERMIT-20260824")
    intent = build_read_only_execution_intent(graph, rec, created_at=CREATED)
    assert validate_execution_intent_binding(graph, replace(intent, external_execution_allowed=True)) is False
    assert validate_execution_intent_binding(graph, replace(intent, consequential=True)) is False


def test_naive_timestamp_and_non_json_payload_fail_closed():
    graph = live_graph()
    rec = action_for(graph, "LIVE-KCL-OMS-PERMIT-20260824")
    try:
        build_read_only_execution_intent(graph, rec, created_at="2026-08-24T08:50:00")
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("naive timestamp accepted")

    try:
        build_read_only_execution_intent(graph, rec, created_at=CREATED, payload={"bad": object()})
    except ValueError as exc:
        assert "canonical JSON" in str(exc)
    else:
        raise AssertionError("non-JSON payload accepted")


def test_canonical_graph_without_live_source_cannot_mint_live_execution_intent():
    graph = canonical_portfolio_graph()
    live = live_graph()
    rec = action_for(live, "LIVE-HYD-GH-REV12-ACK-20260823")
    try:
        build_read_only_execution_intent(graph, rec, created_at=CREATED)
    except ValueError as exc:
        assert "source node not found" in str(exc)
    else:
        raise AssertionError("intent minted without its live evidence source")
