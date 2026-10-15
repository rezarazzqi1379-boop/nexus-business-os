import hashlib
import json
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(RUNTIME))
SRC = os.path.join(REPO, "src")
sys.path.insert(0, RUNTIME)
sys.path.insert(0, SRC)

from control_bridge import ExecutionClass, ExecutionEnvelope, enqueue_from_control
from plo_core import PLOStore
from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.projection import project_projection


def canonical_digest(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_hydro_blocker_drives_read_only_shadow_task_to_verified_completion():
    graph = canonical_portfolio_graph()
    view = project_projection(graph, "PRJ-HYD-01")

    # Brain remains authority-aware: known facts are visible but unresolved unknowns block consequential use.
    assert view["consequential_use_allowed"] is False
    assert view["counts"]["unknowns"] >= 2
    labels = {item["label"] for item in view["requirements"]}
    assert "60 pipes/hour buyer basis" in labels
    assert "Up to 120 MPa duty-dependent" in labels

    unknown_ids = sorted(item["id"] for item in view["unknowns"])
    research_intent = {
        "project_id": "PRJ-HYD-01",
        "purpose": "resolve-hydro-critical-unknowns",
        "unknown_ids": unknown_ids,
        "source_refs": sorted({ref for item in view["requirements"] for ref in item["source_refs"]}),
        "external_effect": False,
    }

    envelope = ExecutionEnvelope(
        project_id="PRJ-HYD-01",
        task_id="hydro-read-only-unknown-resolution",
        decision_ref="BRAIN-V0.2:PRJ-HYD-01:BLOCKED-CONSEQUENTIAL",
        control_ref="FORGE-SHADOW:RESEARCH-TO-RESOLVE-BLOCKER",
        action_digest=canonical_digest(research_intent),
        idempotency_key="shadow:PRJ-HYD-01:resolve-critical-unknowns:v1",
        execution_class=ExecutionClass.SHADOW,
        external_effect=False,
    )

    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "hydro-shadow.db")
        store = PLOStore(db_path)
        run_id = enqueue_from_control(store, envelope)
        claim = store.claim_next("shadow-hydro-worker")
        assert claim and claim["run_id"] == run_id

        result_ref = "BRAIN-V0.2:PRJ-HYD-01:READ-ONLY-PROJECTION-VERIFIED"
        assert store.complete_read_only(run_id, claim["_lease_token"], "shadow-hydro-worker", result_ref) is True
        metrics = store.metrics()
        assert metrics == {
            "duplicate_execution_count": 0,
            "pending": 0,
            "reconciliation_required": 0,
            "completed": 1,
        }

        db = sqlite3.connect(db_path)
        row = db.execute("SELECT action,result FROM audit WHERE run_id=? ORDER BY id DESC LIMIT 1", (run_id,)).fetchone()
        db.close()
        assert row == ("read_only_completed", result_ref)


def main():
    test_hydro_blocker_drives_read_only_shadow_task_to_verified_completion()
    print("1/1 Hydrotester Brain→PLO shadow vertical replay passed")


if __name__ == "__main__":
    main()
