from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from task_handoff import HandoffConflict, HandoffStore, TaskHandoff, TestEvidence

BASE_SHA = "a41f849ec26552a22ec7f6369a8cf51c803b20b6"
HEAD_SHA = "1c85dbbc56370762ffe44ebd682cff2292f06b20"


def handoff(**changes) -> TaskHandoff:
    values = dict(
        task_id="task-example-01",
        owner="claude-code",
        branch="feat/example-v0.1",
        base_sha=BASE_SHA,
        head_sha=HEAD_SHA,
        state="IN_PROGRESS",
        risk_class="LOW",
        review_round=1,
        protected_action_required=False,
        next_deterministic_action="run tests and commit",
    )
    values.update(changes)
    return TaskHandoff(**values)


class TaskHandoffValidationTests(unittest.TestCase):
    def test_valid_handoff_passes(self):
        handoff().validate()

    def test_rejects_invalid_task_id(self):
        with self.assertRaises(ValueError):
            handoff(task_id="Not Safe!").validate()

    def test_rejects_unknown_owner(self):
        with self.assertRaises(ValueError):
            handoff(owner="some-random-bot").validate()

    def test_rejects_non_hex_sha(self):
        with self.assertRaises(ValueError):
            handoff(base_sha="not-a-sha").validate()

    def test_rejects_unknown_state(self):
        with self.assertRaises(ValueError):
            handoff(state="MADE_UP_STATE").validate()

    def test_rejects_unknown_risk_class(self):
        with self.assertRaises(ValueError):
            handoff(risk_class="EXTREME").validate()

    def test_rejects_review_round_below_one(self):
        with self.assertRaises(ValueError):
            handoff(review_round=0).validate()

    def test_rejects_empty_next_action(self):
        with self.assertRaises(ValueError):
            handoff(next_deterministic_action="   ").validate()

    def test_rejects_duplicate_files_changed(self):
        with self.assertRaises(ValueError):
            handoff(files_changed=("a.py", "a.py")).validate()

    def test_rejects_invalid_test_evidence(self):
        bad = TestEvidence(command="pytest", exit_code=0, passed=1, failed=0, errors=0, skipped=0)
        object.__setattr__(bad, "passed", "one")
        with self.assertRaises(ValueError):
            handoff(tests_run=(bad,)).validate()


class TaskHandoffDigestTests(unittest.TestCase):
    def test_identical_handoffs_yield_identical_digest(self):
        first = handoff(created_at="2026-09-03T00:00:00+00:00")
        second = handoff(created_at="2026-09-03T00:00:00+00:00")
        self.assertEqual(first.digest, second.digest)

    def test_changed_state_yields_different_digest(self):
        original = handoff(created_at="2026-09-03T00:00:00+00:00")
        changed = replace(original, state="TESTS_PASSED")
        self.assertNotEqual(original.digest, changed.digest)


class HandoffStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = HandoffStore(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_read_missing_task_returns_none(self):
        self.assertIsNone(self.store.read("no-such-task"))

    def test_claim_then_read_round_trips(self):
        original = handoff()
        self.store.claim(original)
        restored = self.store.read(original.task_id)
        self.assertEqual(restored, original)

    def test_claim_persists_test_evidence(self):
        evidence = TestEvidence(command="pytest -q tests", exit_code=0, passed=110, failed=0, errors=0, skipped=0)
        original = handoff(tests_run=(evidence,))
        self.store.claim(original)
        restored = self.store.read(original.task_id)
        self.assertEqual(restored.tests_run, (evidence,))

    def test_second_owner_cannot_claim_live_task(self):
        self.store.claim(handoff(owner="claude-code", state="IN_PROGRESS"))
        with self.assertRaises(HandoffConflict):
            self.store.claim(handoff(owner="chatgpt-nexus", state="IN_PROGRESS"))

    def test_second_owner_can_claim_after_terminal_state(self):
        self.store.claim(handoff(owner="claude-code", state="IN_PROGRESS"))
        self.store.update(handoff(owner="claude-code", state="DONE"))
        # a terminal state releases the task for a new owner (e.g. a follow-on by the other AI)
        self.store.claim(handoff(owner="chatgpt-nexus", state="IN_PROGRESS"))
        self.assertEqual(self.store.read("task-example-01").owner, "chatgpt-nexus")

    def test_same_owner_can_reclaim_own_in_progress_task(self):
        self.store.claim(handoff(owner="claude-code", state="IN_PROGRESS"))
        self.store.claim(handoff(owner="claude-code", state="TESTS_PASSED"))
        self.assertEqual(self.store.read("task-example-01").state, "TESTS_PASSED")

    def test_update_requires_existing_task(self):
        with self.assertRaises(KeyError):
            self.store.update(handoff())

    def test_update_refuses_cross_owner_write(self):
        self.store.claim(handoff(owner="claude-code"))
        with self.assertRaises(HandoffConflict):
            self.store.update(handoff(owner="chatgpt-nexus", state="DONE"))

    def test_written_file_is_valid_json_with_digest(self):
        path = self.store.claim(handoff())
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("digest", payload)
        self.assertEqual(payload["task_id"], "task-example-01")

    def test_no_mutation_outside_handoff_directory(self):
        before = sorted(p.relative_to(self.temp.name) for p in Path(self.temp.name).rglob("*") if p.is_file())
        self.store.claim(handoff())
        after = sorted(p.relative_to(self.temp.name) for p in Path(self.temp.name).rglob("*") if p.is_file())
        self.assertEqual(len(after), len(before) + 1)
        self.assertTrue(str(after[-1]).replace("\\", "/").startswith(".nexus/handoffs/"))


if __name__ == "__main__":
    unittest.main()
