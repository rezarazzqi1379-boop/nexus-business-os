import json
from pathlib import Path

import pytest

from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.live import LiveEvidenceSignal, apply_live_evidence_signals
from nexus_brain.plo_contract import plo_binding_digest, to_plo_shadow_envelope
from nexus_brain.shadow_loop import build_shadow_intents


SNAPSHOT = Path("data/operational/live_evidence_snapshot_2026-08-24.json")


def _graph_with_live_evidence():
    payload = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    graph = canonical_portfolio_graph()
    apply_live_evidence_signals(graph, [LiveEvidenceSignal(**item) for item in payload["signals"]])
    return graph


def test_kcl_and_hydro_shadow_intents_map_to_plo_without_external_authority():
    intents = build_shadow_intents(_graph_with_live_evidence())
    assert {item.project_id for item in intents} == {"PRJ-KCL-01", "PRJ-HYD-01"}

    envelopes = [
        to_plo_shadow_envelope(
            item,
            decision_ref=f"brain:v0.4:{item.project_id}",
            control_ref="nexus:shadow-loop:v0.5",
        )
        for item in intents
    ]
    assert all(item.execution_class == "SHADOW" for item in envelopes)
    assert all(item.external_effect is False for item in envelopes)
    assert all(item.exact_approval_ref is None for item in envelopes)
    assert all(len(item.idempotency_key) == 64 for item in envelopes)


def test_plo_binding_is_stable_and_changes_when_control_snapshot_changes():
    intent = build_shadow_intents(_graph_with_live_evidence())[0]
    a = to_plo_shadow_envelope(intent, decision_ref="brain:decision:A", control_ref="control:A")
    b = to_plo_shadow_envelope(intent, decision_ref="brain:decision:A", control_ref="control:A")
    c = to_plo_shadow_envelope(intent, decision_ref="brain:decision:A", control_ref="control:B")
    assert a == b
    assert plo_binding_digest(a) == plo_binding_digest(b)
    assert a.idempotency_key != c.idempotency_key
    assert plo_binding_digest(a) != plo_binding_digest(c)


def test_invalid_control_metadata_fails_closed():
    intent = build_shadow_intents(_graph_with_live_evidence())[0]
    with pytest.raises(ValueError):
        to_plo_shadow_envelope(intent, decision_ref="", control_ref="control:A")
    with pytest.raises(ValueError):
        to_plo_shadow_envelope(intent, decision_ref="brain:A", control_ref=" control:A")


def test_adapter_does_not_change_brain_blocker_state():
    graph = _graph_with_live_evidence()
    before = graph.decision_context("PRJ-KCL-01").consequential_use_allowed
    intent = next(item for item in build_shadow_intents(graph) if item.project_id == "PRJ-KCL-01")
    envelope = to_plo_shadow_envelope(intent, decision_ref="brain:decision:kcl", control_ref="control:shadow")
    assert envelope.external_effect is False
    assert graph.decision_context("PRJ-KCL-01").consequential_use_allowed is before is False
