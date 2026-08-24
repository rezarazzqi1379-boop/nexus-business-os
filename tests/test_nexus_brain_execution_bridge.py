from dataclasses import replace

from nexus_brain.command import recommend_internal_actions
from nexus_brain.execution import build_read_only_execution_intent
from nexus_brain.execution_bridge import to_shadow_execution_envelope
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import apply_live_evidence_signals
from nexus_brain.runtime_snapshot import load_manual_snapshot


SNAPSHOT = "data/operational/live_evidence_snapshot_2026-08-24.json"
CREATED = "2026-08-24T08:55:00Z"


def live_graph():
    graph = canonical_portfolio_graph()
    apply_live_evidence_signals(graph, load_manual_snapshot(SNAPSHOT))
    return graph


def build_hyd_intent(graph):
    rec = next(
        item for item in recommend_internal_actions(graph)
        if item.source_node_id == "LIVE-HYD-GH-REV12-ACK-20260823"
    )
    return build_read_only_execution_intent(
        graph,
        rec,
        created_at=CREATED,
        payload={"task": "normalize_supplier_reply", "read_only": True},
    )


def test_valid_execution_intent_maps_to_shadow_only_envelope():
    graph = live_graph()
    intent = build_hyd_intent(graph)
    env = to_shadow_execution_envelope(graph, intent)
    assert env.project_id == "PRJ-HYD-01"
    assert env.task_id == intent.intent_id
    assert env.idempotency_key == intent.intent_id
    assert env.decision_ref == "LIVE-HYD-GH-REV12-ACK-20260823"
    assert env.control_ref == intent.canonical_snapshot_digest
    assert env.action_digest == intent.intent_id[3:]
    assert env.execution_class == "SHADOW"
    assert env.external_effect is False
    assert env.exact_approval_ref is None


def test_stale_intent_cannot_cross_bridge():
    graph = live_graph()
    intent = build_hyd_intent(graph)
    graph.nodes["HYD-PMAX"].attributes["changed_after_intent"] = True
    try:
        to_shadow_execution_envelope(graph, intent)
    except ValueError as exc:
        assert "stale or invalid" in str(exc)
    else:
        raise AssertionError("stale intent crossed the bridge")


def test_field_mutation_to_external_or_consequential_cannot_cross_bridge():
    graph = live_graph()
    intent = build_hyd_intent(graph)
    for changed in (
        replace(intent, external_execution_allowed=True),
        replace(intent, consequential=True),
    ):
        try:
            to_shadow_execution_envelope(graph, changed)
        except ValueError:
            pass
        else:
            raise AssertionError("mutated consequential/external intent crossed shadow bridge")


def test_tampered_intent_id_cannot_cross_bridge():
    graph = live_graph()
    intent = build_hyd_intent(graph)
    tampered = replace(intent, intent_id="EI-" + "0" * 64)
    try:
        to_shadow_execution_envelope(graph, tampered)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered intent id crossed shadow bridge")
