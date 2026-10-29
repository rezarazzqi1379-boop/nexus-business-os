"""Offline structural audit of finite-trial evidence; no network requests."""
from datetime import datetime, timedelta
import re
from nexus_commercial_pilot import SOURCE
from nexus_router_runtime import PROJECT
from source_monitor import LANE
from ted_connector import ENDPOINT


def audit(report):
    attempts, evidence, plan = report["attempts"], report["evidence"], report["plan"]
    assert report["project_id"] == PROJECT and report["authority_status"] == "HOLD"
    assert report["external_commercial_writes"] == 0 and report["scheduler_permanent"] is False
    assert plan["max_attempts"] == 6 and plan["ticks"] == 3 and plan["interval_seconds"] >= 300
    assert len(attempts) <= 6 and report["reserved_attempts"] == len(attempts)
    by_id = {a["attempt_id"]: a for a in attempts}
    assert len(by_id) == len(attempts)
    start = datetime.fromisoformat(plan["starts_at"])
    assert start.tzinfo is not None
    for a in attempts:
        assert a["trial_id"] == report["trial_id"] and type(a["tick"]) is int and 0 <= a["tick"] < 3
        assert a["source"] in {"worldbank","ted"}
        stamp = datetime.fromisoformat(a["reserved_at"])
        target = start + timedelta(seconds=a["tick"]*plan["interval_seconds"])
        assert target <= stamp < target + timedelta(seconds=plan["interval_seconds"])
    assert len({e["attempt_id"] for e in evidence}) == len(evidence)
    keys = set()
    collection_pairs = set()
    for e in evidence:
        a = by_id[e["attempt_id"]]
        assert (e["tick"],e["provider"]) == (a["tick"],a["source"])
        assert e["project_id"] == PROJECT and e["lane_id"] == LANE and e["trial_id"] == report["trial_id"]
        assert e["evidence_class"] == "CLAIM" and e["authority_status"] == "HOLD"
        assert e["source_url"] == (SOURCE if e["provider"] == "worldbank" else ENDPOINT)
        assert re.fullmatch(r"[0-9a-f]{64}",e["source_sha256"])
        assert e["source_mode"] == plan["source_mode"] == "REAL_PUBLIC_HTTP"
        assert e["raw_count"] == len(e["records"]) <= 3
        if e["raw_count"]:
            collection_pairs.add((e["tick"],e["provider"]))
        for row in e["records"]:
            keys.add((e["provider"],row["identity"]))
    return {"structural_audit": "PASS", "reserved_attempts": len(attempts),
            "responses_with_evidence": len(evidence), "distinct_source_notice_ids": len(keys),
            "nonempty_collection_pairs": sorted(collection_pairs),
            "clean_three_tick_collection_proven": len(collection_pairs) == 6,
            "independent_commercial_claim_verified": False,
            "scope": "STRUCTURAL_LEDGER_AUDIT_NOT_RAW_RESPONSE_REPLAY"}
