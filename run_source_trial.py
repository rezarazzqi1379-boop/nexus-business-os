"""Finite local host: three ticks, six total reserved requests, then exit."""
import argparse
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from time import sleep

from autonomy import AutonomyStore
from nexus_commercial_pilot import SOURCE, parse_source, notice_url, get_public_notices
from nexus_router_runtime import PROJECT
from source_monitor import LANE
from ted_connector import ENDPOINT, QUERY, REQUEST, public_search, parse_notices


def run_tick(store, trial_id, tick, *, transports=None, now=None):
    observed = now or datetime.now(timezone.utc)
    frozen = transports is not None
    providers = transports if frozen else {"worldbank": get_public_notices, "ted": public_search}
    plan = store.http_trial_plan(trial_id, PROJECT)
    if plan["sources"] != ["ted", "worldbank"]:
        raise ValueError("trial_sources_mismatch")
    old = store.http_trial_evidence(trial_id, PROJECT)
    expected_mode = "FROZEN_TEST_FIXTURE" if frozen else "REAL_PUBLIC_HTTP"
    if plan["source_mode"] != expected_mode:
        raise ValueError("trial_source_mode_mismatch")
    if any(e["source_mode"] != expected_mode for e in old):
        raise ValueError("trial_source_mode_mismatch")
    for source, endpoint, group in (("worldbank", SOURCE, "worldbank-publication"),
                                    ("ted", ENDPOINT, "eu-publications-office")):
        if any(e["tick"] == tick and e["provider"] == source for e in old):
            continue
        try:
            attempt = store.reserve_http_attempt(trial_id, PROJECT, tick=tick, source=source,
                now=observed if frozen else datetime.now(timezone.utc))
        except PermissionError:
            continue
        try:
            body = providers[source](endpoint)
            if type(body) is not bytes or len(body) > 65536:
                raise ValueError("response_bounds")
        except Exception:
            store.finish_http_attempt(attempt, success=False)
            continue
        store.finish_http_attempt(attempt, success=True)
        try:
            rows = (tuple({"identity": r["id"], "url": notice_url(r["id"])} for r in parse_source(body))
                    if source == "worldbank" else parse_notices(body))
        except (ValueError, TypeError, KeyError):
            continue  # Received but invalid evidence remains visible, never retry for free.
        stamp = observed.isoformat() if frozen else datetime.now(timezone.utc).isoformat()
        store.record_http_evidence(attempt, {"attempt_id": attempt, "trial_id": trial_id,
            "project_id": PROJECT, "lane_id": LANE, "tick": tick, "provider": source,
            "source_url": endpoint, "query": "steel World Bank" if source == "worldbank" else QUERY,
            "request_method": "GET" if source == "worldbank" else "POST_READ_ONLY_SEARCH",
            "request_body": None if source == "worldbank" else REQUEST,
            "source_sha256": sha256(body).hexdigest(), "retrieved_at": stamp,
            "independence_group": group, "source_mode": expected_mode,
            "records": list(rows), "raw_count": len(rows),
            "unique_count": len({r["identity"] for r in rows}),
            "evidence_class": "CLAIM", "decision": "INVESTIGATE",
            "shared_claim_verification": "NOT_ESTABLISHED", "authority_status": "HOLD"})
    return report(store, trial_id)


def report(store, trial_id):
    attempts = store.http_trial_attempts(trial_id, PROJECT)
    evidence = store.http_trial_evidence(trial_id, PROJECT)
    pairs = {(e["tick"], e["provider"]) for e in evidence if e["source_mode"] == "REAL_PUBLIC_HTTP"}
    complete = pairs == {(t, s) for t in range(3) for s in ("worldbank", "ted")}
    nonempty = {e["provider"] for e in evidence if e["source_mode"] == "REAL_PUBLIC_HTTP" and e["raw_count"] > 0}
    return {"trial_id": trial_id, "project_id": PROJECT, "plan": store.http_trial_plan(trial_id, PROJECT),
            "attempts": attempts, "reserved_attempts": len(attempts), "evidence": evidence,
            "all_tick_responses_received": complete,
            "multi_source_live_proven": complete and nonempty == {"worldbank", "ted"},
            "independent_shared_claim_verified": False, "authority_status": "HOLD",
            "external_commercial_writes": 0, "scheduler_permanent": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--live", action="store_true", required=True)
    args = parser.parse_args()
    store = AutonomyStore(args.db)
    try:
        plan = store.http_trial_plan(args.trial_id, PROJECT)
        start = datetime.fromisoformat(plan["starts_at"])
    except PermissionError:
        start = datetime.now(timezone.utc)
        store.configure_http_trial(args.trial_id, PROJECT, sources=("worldbank", "ted"), starts_at=start,
                                   source_mode="REAL_PUBLIC_HTTP")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for tick in range(3):
        target = start + timedelta(seconds=300*tick)
        while (target - datetime.now(timezone.utc)).total_seconds() > 0:
            sleep(min(10, (target-datetime.now(timezone.utc)).total_seconds()))
        result = run_tick(store, args.trial_id, tick)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"tick": tick, "reserved_attempts": result["reserved_attempts"],
                          "evidence_count": len(result["evidence"])}), flush=True)
    print("FINITE_TRIAL_EXIT", flush=True)
    return 0 if result["multi_source_live_proven"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
