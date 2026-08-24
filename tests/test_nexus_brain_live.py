import json
from dataclasses import replace
from pathlib import Path

from nexus_brain.command import recommend_internal_actions
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import LiveEvidenceSignal, action_required_signals, apply_live_evidence_signals
from nexus_brain.projection import project_projection


SNAPSHOT = Path("data/operational/live_evidence_snapshot_2026-08-24.json")


def load_signals():
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert payload["snapshot_mode"] == "MANUAL_CONNECTOR_READ_ONLY"
    assert payload["continuous_sync"] is False
    return [LiveEvidenceSignal(**item) for item in payload["signals"]]


def test_live_snapshot_adds_tier_b_communications_without_rewriting_canonical_requirements():
    graph = canonical_portfolio_graph()
    before = {
        "hyd": next(n for n in graph.nodes.values() if n.id == "HYD-PMAX").attributes["value"],
        "kcl": next(n for n in graph.nodes.values() if n.id == "KCL-K2O").attributes["value"],
    }
    apply_live_evidence_signals(graph, load_signals())
    assert graph.nodes["HYD-PMAX"].attributes["value"] == before["hyd"] == 120
    assert graph.nodes["KCL-K2O"].attributes["value"] == before["kcl"] == 61
    assert graph.nodes["LIVE-KCL-OMS-PERMIT-20260824"].authority_tier.value == "live_evidence"
    assert graph.nodes["LIVE-KCL-OMS-PERMIT-20260824"].epistemic_status.value == "fact"


def test_live_snapshot_provenance_is_retrievable():
    graph = apply_live_evidence_signals(canonical_portfolio_graph(), load_signals())
    assert graph.trace_provenance("LIVE-KCL-EUROCHEM-20260824") == ("gmail:1a032944cf64e85f",)
    assert graph.trace_provenance("LIVE-HYD-GH-REV12-ACK-20260823") == ("gmail:1a02f17fe9dd0b73",)


def test_action_required_queue_surfaces_oms_and_gh_without_sending_anything():
    graph = apply_live_evidence_signals(canonical_portfolio_graph(), load_signals())
    ids = {node.id for node in action_required_signals(graph)}
    assert "LIVE-KCL-OMS-PERMIT-20260824" in ids
    assert "LIVE-HYD-GH-REV12-ACK-20260823" in ids
    assert "LIVE-CAN-GE-SPEED-20260820" not in ids


def test_live_communication_facts_do_not_clear_existing_blocking_unknowns():
    graph = apply_live_evidence_signals(canonical_portfolio_graph(), load_signals())
    kcl = project_projection(graph, "PRJ-KCL-01")
    hyd = project_projection(graph, "PRJ-HYD-01")
    assert kcl["consequential_use_allowed"] is False
    assert hyd["consequential_use_allowed"] is False
    assert "blocking_unknown" in kcl["blockers"]
    assert "blocking_unknown" in hyd["blockers"]


def test_duplicate_live_evidence_fails_closed():
    graph = canonical_portfolio_graph()
    signals = load_signals()
    apply_live_evidence_signals(graph, signals)
    try:
        apply_live_evidence_signals(graph, signals[:1])
    except ValueError as exc:
        assert "duplicate live evidence" in str(exc)
    else:
        raise AssertionError("duplicate connector evidence must fail closed")


def test_unknown_project_fails_closed():
    graph = canonical_portfolio_graph()
    signal = replace(load_signals()[0], project_id="PRJ-NOT-REAL")
    try:
        apply_live_evidence_signals(graph, [signal])
    except ValueError as exc:
        assert "unknown project" in str(exc)
    else:
        raise AssertionError("cross-project/unscoped evidence must fail closed")


def test_naive_or_invalid_observed_at_fails_closed():
    for value in ("2026-08-24T08:00:00", "not-a-time", ""):
        graph = canonical_portfolio_graph()
        signal = replace(load_signals()[0], observed_at=value)
        try:
            apply_live_evidence_signals(graph, [signal])
        except ValueError:
            pass
        else:
            raise AssertionError("ambiguous observed_at accepted")


def test_non_boolean_action_required_fails_closed():
    graph = canonical_portfolio_graph()
    signal = replace(load_signals()[0], action_required="true")
    try:
        apply_live_evidence_signals(graph, [signal])
    except ValueError as exc:
        assert "boolean" in str(exc)
    else:
        raise AssertionError("truthy non-boolean action_required accepted")


def test_control_and_format_characters_in_metadata_fail_closed():
    for field, bad in (("id", "LIVE-BAD\nX"), ("source_ref", "gmail:\u202eabc"), ("topic", "permit\nadmin")):
        graph = canonical_portfolio_graph()
        signal = replace(load_signals()[0], **{field: bad})
        try:
            apply_live_evidence_signals(graph, [signal])
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsafe {field} accepted")


def test_malformed_signal_object_fails_closed():
    graph = canonical_portfolio_graph()
    try:
        apply_live_evidence_signals(graph, [{"id": "not-a-signal"}])
    except ValueError:
        pass
    else:
        raise AssertionError("malformed signal object accepted")


def test_command_recommendations_are_internal_only_and_deterministic():
    graph = apply_live_evidence_signals(canonical_portfolio_graph(), load_signals())
    actions = recommend_internal_actions(graph)
    by_source = {item.source_node_id: item for item in actions}
    oms = by_source["LIVE-KCL-OMS-PERMIT-20260824"]
    gh = by_source["LIVE-HYD-GH-REV12-ACK-20260823"]
    assert oms.action == "verify_permit_authority_and_current_buyer_status"
    assert oms.priority_class == "P0_EVIDENCE_BLOCKER"
    assert gh.action == "normalize_supplier_reply_against_canonical_qualification_matrix"
    assert gh.priority_class == "P0_NEW_PRIMARY_EVIDENCE"
    assert all(item.external_execution_allowed is False for item in actions)
