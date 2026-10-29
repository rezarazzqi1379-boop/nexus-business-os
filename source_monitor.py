"""Bounded monitor tick over the existing durable commercial research runtime.

No daemon or provider activation. The host calls tick; the existing queue owns
leases, retries, cancellation, checkpoints and supervisor review.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextvars import ContextVar
from nexus_http_attempt_budget import AttemptBudget, budgeted_transport
from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
from time import monotonic
import json
import uuid

from nexus_commercial_pilot import CommercialRuntime, SOURCE, LANE, parse_source, notice_url
from nexus_connector_control_plane import (
    ConnectorControlPlane, ConnectorManifest, ConnectorSnapshot, ConnectorState,
    EvidenceEnvelope, EvidenceClass,
)
from nexus_router_runtime import PROJECT


class MonitoringRuntime(CommercialRuntime):
    action = "router.source-monitor.v1"

    def __init__(self, path, *, transport=None, attempt_budget: AttemptBudget | None = None):
        from nexus_commercial_pilot import get_public_notices
        if attempt_budget is not None and not isinstance(attempt_budget, AttemptBudget):
            raise TypeError("invalid_attempt_budget")
        # Live mode cannot bypass durable pre-request reservations.
        # Fixture transports remain isolated and may opt in for tests.
        if transport is None and attempt_budget is None:
            from pathlib import Path
            attempt_budget = AttemptBudget(str(Path(path)) + ".http-attempts.sqlite",
                                           scope="nexus:worldbank:bounded-live", max_attempts=6)
        self.attempt_budget = attempt_budget
        self._budget_task = ContextVar("nexus_monitor_budget_task", default=None)
        underlying = get_public_notices if transport is None else transport
        if attempt_budget is not None:
            def guarded(url):
                task_id = self._budget_task.get()
                if task_id is None:
                    raise PermissionError("budgeted_transport_requires_task_context")
                return budgeted_transport(attempt_budget, tick_id=task_id, transport=underlying)(url)
            effective_transport = guarded
        else:
            effective_transport = underlying
        self.source_mode = "REAL_PUBLIC_HTTP" if transport is None else "FROZEN_TEST_FIXTURE"
        super().__init__(path, transport=effective_transport)
        with closing(self.store._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT body FROM router_events WHERE project=? AND kind='monitor_mode'",
                               (PROJECT,)).fetchall()
            if prior and any(json.loads(row[0])["source_mode"] != self.source_mode for row in prior):
                raise ValueError("separate_database_required_for_source_mode")
            if not prior:
                self._event(db, "control", "monitor_mode", {"source_mode": self.source_mode},
                            datetime.now(timezone.utc))
            db.commit()

    def execute(self, payload):
        token = self._budget_task.set(payload["task_id"])
        try:
            return {**super().execute(payload), "source_mode": self.source_mode}
        finally:
            self._budget_task.reset(token)

    def validate_result(self, payload, result):
        super().validate_result(payload, result)
        if result.get("source_mode") != self.source_mode:
            raise ValueError("source_mode_mismatch")


def _time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class SourceObservation:
    """Trusted adapter binding; source text cannot grant authority or independence.

    independence_group is operator-reviewed ownership/origin, not a hostname.
    None means unknown. Two mirrors must share a group.
    """
    manifest: ConnectorManifest
    independence_group: str | None
    evidence: tuple[EvidenceEnvelope, ...]
    snapshot: ConnectorSnapshot


def compare_sources(observations, *, now, project_id=PROJECT, lane_id=LANE):
    """Compare scoped exact claims, never promote CLAIM to FACT or allow action."""
    observations = tuple(observations)
    if not 1 <= len(observations) <= 4:
        raise ValueError("source_budget_exceeded")
    evidence = []
    for source in observations:
        if "read" not in source.manifest.authority_scope:
            raise ValueError("read_authority_required")
        if len(source.evidence) > 3:
            raise ValueError("result_budget_exceeded")
        if source.snapshot.connector_id != source.manifest.connector_id:
            raise ValueError("snapshot_binding_mismatch")
        for item in source.evidence:
            if not item.semantic_key.startswith(lane_id + ":notice:"):
                raise ValueError("lane_binding_mismatch")
            if item.connector_id != source.manifest.connector_id:
                raise ValueError("evidence_binding_mismatch")
            if item.classification is not EvidenceClass.CLAIM:
                raise ValueError("source_must_remain_claim")
            evidence.append(item)
    preflight = ConnectorControlPlane(s.manifest for s in observations).preflight(
        project_id=project_id, snapshots=[s.snapshot for s in observations],
        evidence=evidence, required_connectors=[s.manifest.connector_id for s in observations], now=now)
    claims = []
    for key in sorted({e.semantic_key for e in evidence}):
        members = [e for e in evidence if e.semantic_key == key]
        groups = {s.independence_group for s in observations if s.independence_group
                  and any(e.semantic_key == key for e in s.evidence)}
        conflict = len({e.value_digest for e in members}) > 1
        status = ("CONFLICT" if conflict else "CORROBORATED_CLAIM" if len(groups) >= 2
                  else "INDEPENDENT_SOURCE_MISSING")
        if preflight["gate"] == "BLOCK":
            status = "BLOCKED"
        claims.append({"semantic_key": key, "status": status,
                       "decision": "REJECT" if conflict or status == "BLOCKED" else "INVESTIGATE",
                       "evidence_ids": sorted(e.evidence_id for e in members),
                       "independent_groups": len(groups), "evidence_class": "CLAIM"})
    return {"preflight": preflight, "claims": claims, "external_action_authorized": False}


def source_provenance(result):
    """Bind retained source bytes and every discovered notice to the fixed lane."""
    doc = result["documents"][0]
    body = doc["body"].encode()
    if doc["url"] != SOURCE or sha256(body).hexdigest() != doc["sha256"]:
        raise ValueError("source_binding_mismatch")
    return [{"project_id": PROJECT, "lane_id": LANE, "provider": "worldbank",
             "query": "steel World Bank", "source_url": SOURCE,
             "discovered_url": notice_url(row["id"]), "retrieved_at": result["observed_at"],
             "source_sha256": doc["sha256"], "status": "CANDIDATE_NOT_ACTIVATED"}
            for row in parse_source(body)]


def tick(runtime: MonitoringRuntime, *, now: str, interval_seconds=3600):
    """Enqueue a UTC bucket once, drain eligible work and review its checkpoint.

    A crash/retry can repeat a read; this is not exactly-once HTTP delivery.
    Existing retry backoff/max attempts and emergency stop remain authoritative.
    """
    if not isinstance(runtime, MonitoringRuntime):
        raise TypeError("monitor_runtime_required")
    if type(interval_seconds) is not int or not 300 <= interval_seconds <= 86400:
        raise ValueError("invalid_monitor_interval")
    current = _time(now)
    actual = datetime.now(timezone.utc)
    if abs((actual - current).total_seconds()) > 300:
        raise ValueError("tick_clock_outside_window")
    mode_key = "live" if runtime.source_mode == "REAL_PUBLIC_HTTP" else "fixture"
    task = f"monitor_{mode_key}_{interval_seconds}_{int(current.timestamp()) // interval_seconds}"
    started = monotonic()
    submitted = runtime.submit(task, budget_units=3)
    completed = 0
    owner = "monitor_" + uuid.uuid4().hex
    item = runtime.claim(owner)
    if item is not None:
        try:
            runtime.finish(item, owner, runtime.execute(item.payload))
            completed = 1
        except Exception:
            try:
                runtime.fail(item, owner)
            except PermissionError:
                pass  # Stop/cancellation/lease fencing wins.
    try:
        review = runtime.review(task)
    except (ValueError, KeyError, TypeError):
        review = "stale_or_invalid"
    with closing(runtime.store._connect()) as db:
        checkpoints = [json.loads(row[0]) for row in db.execute(
            "SELECT body FROM router_events WHERE project=? AND task=? AND kind='checkpoint' ORDER BY seq",
            (PROJECT, task)).fetchall()]
    result = checkpoints[-1] if checkpoints else None
    provenance = source_provenance(result) if result and review == "accepted" else []
    comparison = None
    if result and review == "accepted":
        observed = result["observed_at"]
        manifest = ConnectorManifest("worldbank", "World Bank notices", ("read",), (PROJECT,), True, False, 300)
        envelopes = tuple(EvidenceEnvelope(
            a["opportunity_id"], "worldbank", PROJECT, LANE + ":notice:" + a["opportunity_id"],
            a["source_record_sha256"], EvidenceClass.CLAIM, a["source_url"], observed)
            for a in result["values"]["assessments"])
        comparison = compare_sources((SourceObservation(manifest, None, envelopes,
            ConnectorSnapshot("worldbank", observed, ConnectorState.AVAILABLE)),),
            now=datetime.now(timezone.utc).isoformat())
    return {"schema_version": "nexus.source-monitor.v1", "project_id": PROJECT, "lane_id": LANE,
            "source_mode": runtime.source_mode,
            "task_id": task, "submitted": submitted, "completed_queue_items": completed,
            "supervisor": review, "status": "ACCEPTED" if provenance or result and review == "accepted" else "WAITING_OR_BLOCKED",
            "provenance": provenance, "assessment": result["values"] if review == "accepted" and result else None,
            "source_comparison": comparison, "work_attempted": item is not None,
            "elapsed_seconds": monotonic() - started, "source_count": 1,
            "independent_verification": "INDEPENDENT_SOURCE_MISSING", "external_writes": 0,
            "scheduler_active": False, "authority_status": "HOLD"}


def main():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", type=Path)
    mode.add_argument("--live", action="store_true", help="One bounded allowlisted public read per eligible attempt")
    parser.add_argument("--interval-seconds", type=int, default=3600)
    args = parser.parse_args()
    if args.fixture:
        from nexus_commercial_pilot import MAX_BYTES
        with args.fixture.open("rb") as stream:
            fixture = stream.read(MAX_BYTES + 1)
        parse_source(fixture)
        transport = lambda url: fixture
    else:
        transport = None
    result = tick(MonitoringRuntime(args.db, transport=transport),
                  now=datetime.now(timezone.utc).isoformat(), interval_seconds=args.interval_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "task_id", "source_mode", "supervisor")}))
    return 0 if result["status"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
