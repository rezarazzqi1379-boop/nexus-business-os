"""Frozen synthetic ablation; no live commercial outcome or model use implied."""
import json
import subprocess
import sys
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from commercial_relationship_proof import prove_relationship
from tests.test_commercial_relationship_proof import NOW, fixture

BASELINE = "caf79562197c24f6f061defb3c40a7f5031a9bdd"


def benchmark():
    # Execute the actual pre-change gate, rather than reconstructing a baseline.
    code = subprocess.check_output(["git", "show", f"{BASELINE}:steel_commercial_intelligence.py"], cwd=ROOT, text=True)
    baseline = {"__name__": "frozen_commercial_baseline"}
    exec(compile(code, f"{BASELINE}:steel_commercial_intelligence.py", "exec"), baseline)
    observations, reviews = fixture()
    cases = [dict(name="reviewed-current", expected=True, observations=observations, reviews=reviews)]
    cases.append(dict(name="no-review", expected=False, observations=observations, reviews=()))
    cases.append(dict(name="stale", expected=False, observations=tuple(replace(o, observed_at="2025-01-01T00:00:00+00:00") for o in observations), reviews=reviews))
    cases.append(dict(name="wrong-legal-id", expected=False, observations=tuple(replace(o, payload=o.payload.replace(b"TEST-123", b"TEST-124")) for o in observations), reviews=reviews))
    cases.append(dict(name="changed-digest", expected=False, observations=tuple(replace(o, payload=o.payload+b" ") for o in observations), reviews=reviews))
    cases.append(dict(name="copied-publisher", expected=False, observations=tuple(replace(o, origin_id="same") for o in observations), reviews=tuple(replace(r, origin_id="same") for r in reviews)))
    cases.append(dict(name="duplicate", expected=False, observations=(observations[0], observations[0]), reviews=reviews))
    cases.append(dict(name="cross-project", expected=False, observations=(observations[0], replace(observations[1], project_id="OTHER")), reviews=reviews))
    results = []
    proof = None
    for case in cases:
        # Existing gate's documented input: caller-provided OBSERVED/current edges.
        edges = tuple(baseline["IntelEdge"](o.project_id, "buyer-fixture", "CURRENT_RFQ", "forged-shaft", o.source_ref, o.observed_at, baseline["EvidenceKind"].OBSERVED, True) for o in case["observations"])
        old = baseline["current_demand_ready"](edges, "SANDBOX", "buyer-fixture", "forged-shaft")
        try:
            result = prove_relationship(case["observations"], project_id="SANDBOX", lane="commercial-proof", buyer_id="buyer-fixture", product_id="forged-shaft", legal_identities={"buyer-fixture":"TEST-123"}, reviews=case["reviews"], as_of=NOW)
            new = result.ready_for_research
            if case["name"] == "reviewed-current":
                proof = dict(graph=[asdict(e) for e in result.graph],
                             evidence_digests=[r.digest for r in result.history],
                             extraction_bytes=result.extraction_bytes,
                             extraction_count=result.extraction_count,
                             ready_for_research=result.ready_for_research)
        except ValueError:
            new = False
        results.append(dict(case=case["name"], expected=case["expected"], baseline=old, candidate=new))
    def metrics(key):
        tp = sum(r[key] and r["expected"] for r in results)
        fp = sum(r[key] and not r["expected"] for r in results)
        return dict(decision_accuracy=sum(r[key] == r["expected"] for r in results)/len(results),
                    true_accepted=tp, false_accepted=fp,
                    verified_relationship_precision=tp/(tp+fp) if tp+fp else None,
                    verified_relationship_yield=tp/len(results), model_tokens=0)
    # Direct field extraction check against independently stated fixture values.
    expected = {"buyer_id":"buyer-fixture", "legal_id":"TEST-123", "product_id":"forged-shaft", "relation":"CURRENT_RFQ"}
    fields_correct = sum(json.loads(o.payload).get(k) == v for o in observations for k,v in expected.items())
    return dict(schema="nexus.commercial-proof-benchmark.v1", baseline_sha=BASELINE,
                baseline_module_sha256=sha256(code.encode()).hexdigest(), proof=proof,
                corpus="fictional structured fixtures; eight cases, not a market sample",
                as_of=NOW, cases=results, baseline=metrics("baseline"), candidate=metrics("candidate"),
                extraction=dict(correct_fields=fields_correct, total_fields=8, accuracy=fields_correct/8,
                                method="deterministic JSON; no unstructured extraction evaluated"),
                provider_token_usage=None, agent_session_token_usage=None,
                commercial_outcomes=0, maturity="EXPERIMENT_ONLY")


if __name__ == "__main__":
    result = benchmark()
    target = ROOT / "data/research/commercial-relationship-benchmark.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
