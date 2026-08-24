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


def test_kcl_blockers_drive_read_only_shadow_task_to_verified_completion():
    graph = canonical_portfolio_graph()
    view = project_projection(graph, "PRJ-KCL-01")

    assert view["consequential_use_allowed"] is False
    assert view["counts"]["unknowns"] >= 3
    labels = {item["label"] for item in view["requirements"]}
    assert "K2O min 61%" in labels
    assert "Moisture max 0.5%" in labels

    unknown_ids = sorted(item["id"] for item in view["unknowns"])
    assert "KCL-UNK-DEMAND" in unknown_ids
    assert "KCL-UNK-PERMIT" in unknown_ids
    assert "KCL-UNK-COMM" in unknown_ids

    research_intent = {
        "project_id": "PRJ-KCL-01",
        "purpose": "resolve-kcl-commercial-and-permit-blockers",
        "unknown_ids": unknown_ids,
        "source_refs": sorted({ref for item in view["requirements"] for ref in item["source_refs"]}),
        "external_effect": False,
    }

    envelope = ExecutionEnvelope(
        project_id="PRJ-KCL-01",
        task_id="kcl-read-only-blocker-resolution",
        decision_ref="BRAIN-V0.2:PRJ-KCL-01:BLOCKED-CONSEQUENTIAL",
        control_ref="FORGE-SHADOW:RESEARCH-TO-RESOLVE-BLOCKER",
        action_digest=canonical_digest(research_intent),
        idempotency_key="shadow:PRJ-KCL-01:resolve-commercial-permit-blockers:v1",
        execution_class=ExecutionClass.SHADOW,
        external_effect=False,
    )

    with tempfile.TemporaryDirectory() as td:
        db_path = os.path.join(td, "kcl-shadow.db")
        store = PLOStore(db_path)
        first_run = enqueue_from_control(store, envelope)
        second_run = enqueue_from_control(store, envelope)
        assert first_run == second_run

        claim = store.claim_next("shadow-kcl-worker")
        assert claim and claim["run_id"] == first_run

        result_ref = "BRAIN-V0.2:PRJ-KCL-01:READ-ONLY-BLOCKER-PACKET-VERIFIED"
        assert store.complete_read_only(first_run, claim["_lease_token"], "shadow-kcl-worker", result_ref) is True
        metrics = store.metrics()
        assert metrics == {
            "duplicate_execution_count": 0,
            "pending": 0,
            "reconciliation_required": 0,
            "completed": 1,
        }

        db = sqlite3.connect(db_path)
        audit = db.execute("SELECT action,result FROM audit WHERE run_id=? ORDER BY id DESC LIMIT 1", (first_run,)).fetchone()
        task = db.execute("SELECT status,retry_count,approval_required FROM tasks WHERE run_id=?", (first_run,)).fetchone()
        db.close()
        assert audit == ("read_only_completed", result_ref)
        assert task == ("COMPLETED", 0, 0)


def main():
    test_kcl_blockers_drive_read_only_shadow_task_to_verified_completion()
    print("1/1 KCl Brain→PLO shadow vertical replay passed")


if __name__ == "__main__":
    main()
