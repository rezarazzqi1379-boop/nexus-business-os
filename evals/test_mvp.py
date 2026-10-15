from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from threading import Barrier, Thread
from datetime import datetime, timedelta, timezone
from pathlib import Path

from approvals import ApprovalRequest, ApprovalStore
from audit import AuditLog
from contracts import EventEnvelope, EvidenceClass, EvidenceRecord


NOW = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)


class ContractTests(unittest.TestCase):
    def test_event_is_versioned_and_deterministic(self):
        value = {"event_id": "evt_1", "project_id": "kcl_mop", "event_type": "email.received",
                 "source": "gmail", "occurred_at": "2026-08-20T12:00:00Z",
                 "received_at": "2026-08-20T12:00:01Z", "payload": {"thread": "t1"}}
        self.assertEqual(EventEnvelope.from_dict(value).digest, EventEnvelope.from_dict(value).digest)

    def test_event_rejects_naive_time(self):
        value = {"event_id": "e", "project_id": "p", "event_type": "x", "source": "s",
                 "occurred_at": "2026-08-20T12:00:00", "received_at": "2026-08-20T12:00:01Z", "payload": {}}
        with self.assertRaisesRegex(ValueError, "timezone"):
            EventEnvelope.from_dict(value)

    def test_fact_requires_source(self):
        with self.assertRaisesRegex(ValueError, "fact_requires_source"):
            EvidenceRecord("e", "p", EvidenceClass.FACT, "statement", "", NOW.isoformat(), .9)


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ApprovalStore(Path(self.temp.name) / "state.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_action_is_consumed_once(self):
        request = ApprovalRequest("kcl_mop", "send", "supplier@example.com", {"draft_id": "d1"}, "operator")
        approval_id = self.store.request(request, now=NOW)
        self.assertEqual(self.store.decide(approval_id, approved=True, decided_by="reza", now=NOW), "approved")
        self.assertTrue(self.store.consume(approval_id, action_digest=request.action_digest, now=NOW))
        self.assertFalse(self.store.consume(approval_id, action_digest=request.action_digest, now=NOW))

    def test_changed_target_cannot_reuse_approval(self):
        first = ApprovalRequest("kcl_mop", "send", "a@example.com", {"draft_id": "d1"}, "operator")
        changed = ApprovalRequest("kcl_mop", "send", "b@example.com", {"draft_id": "d1"}, "operator")
        approval_id = self.store.request(first, now=NOW)
        self.store.decide(approval_id, approved=True, decided_by="reza", now=NOW)
        self.assertFalse(self.store.consume(approval_id, action_digest=changed.action_digest, now=NOW))

    def test_expired_approval_fails_closed(self):
        request = ApprovalRequest("p", "deploy", "production", {}, "operator", ttl_seconds=10)
        approval_id = self.store.request(request, now=NOW)
        self.assertEqual(self.store.decide(approval_id, approved=True, decided_by="reza", now=NOW + timedelta(seconds=11)), "expired")

    def test_concurrent_decisions_allow_exactly_one_winner(self):
        request = ApprovalRequest("p", "send", "recipient@example.com", {}, "operator")
        approval_id = self.store.request(request, now=NOW)
        barrier = Barrier(2)
        outcomes: list[tuple[str, str]] = []

        def decide(approved: bool, reviewer: str) -> None:
            barrier.wait()
            try:
                status = self.store.decide(approval_id, approved=approved, decided_by=reviewer, now=NOW)
                outcomes.append(("ok", status))
            except ValueError as exc:
                outcomes.append(("error", str(exc)))

        threads = [
            Thread(target=decide, args=(True, "reviewer-a")),
            Thread(target=decide, args=(False, "reviewer-b")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(sum(kind == "ok" for kind, _ in outcomes), 1)
        self.assertEqual(sum(value == "approval_not_pending" for _, value in outcomes), 1)


class AuditTests(unittest.TestCase):
    def test_hash_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.db"
            log = AuditLog(path)
            log.append("operator", "event.received", {"id": "e1"}, occurred_at=NOW)
            log.append("worker", "draft.created", {"id": "d1"}, occurred_at=NOW)
            self.assertTrue(log.verify())
            with closing(sqlite3.connect(path)) as db:
                with db:
                    db.execute("UPDATE audit_log SET body_json='{}' WHERE sequence=1")
            self.assertFalse(log.verify())


if __name__ == "__main__":
    unittest.main()
