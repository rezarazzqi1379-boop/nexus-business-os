import tempfile
import unittest
from pathlib import Path

from state import EventRecord, EventStore


class VNextEventIsolationTests(unittest.TestCase):
    def _store(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return EventStore(Path(temp.name) / "events.sqlite")

    def test_duplicate_requires_same_project_identity(self):
        store = self._store()
        original = EventRecord("evt-1", "hydrostatic_tester", "gmail_received", {"message_id": "m-1"})
        store.begin(original)

        contaminated = EventRecord("evt-1", "kcl_mop", "gmail_received", {"message_id": "m-1"})
        with self.assertRaisesRegex(ValueError, "event_id_project_mismatch"):
            store.begin(contaminated)

    def test_duplicate_requires_same_event_type(self):
        store = self._store()
        original = EventRecord("evt-2", "hydrostatic_tester", "gmail_received", {"message_id": "m-2"})
        store.begin(original)

        replay_as_action = EventRecord("evt-2", "hydrostatic_tester", "external_action", {"message_id": "m-2"})
        with self.assertRaisesRegex(ValueError, "event_id_type_mismatch"):
            store.begin(replay_as_action)

    def test_exact_replay_remains_idempotent(self):
        store = self._store()
        event = EventRecord("evt-3", "hydrostatic_tester", "gmail_received", {"message_id": "m-3"})
        self.assertEqual(store.begin(event), "new")
        self.assertEqual(store.begin(event), "duplicate")

    def test_same_identity_with_mutated_payload_is_rejected(self):
        store = self._store()
        store.begin(EventRecord("evt-4", "hydrostatic_tester", "vendor_claim", {"pressure_mpa": 120}))

        with self.assertRaisesRegex(ValueError, "event_id_payload_mismatch"):
            store.begin(EventRecord("evt-4", "hydrostatic_tester", "vendor_claim", {"pressure_mpa": 70}))

    def test_retryable_error_only_retries_same_event_identity(self):
        store = self._store()
        event = EventRecord("evt-5", "hydrostatic_tester", "gmail_received", {"message_id": "m-5"})
        self.assertEqual(store.begin(event), "new")
        store.set_status("evt-5", "retryable_error")
        self.assertEqual(store.begin(event), "retry")

        store.set_status("evt-5", "retryable_error")
        with self.assertRaisesRegex(ValueError, "event_id_project_mismatch"):
            store.begin(EventRecord("evt-5", "can_forming", "gmail_received", {"message_id": "m-5"}))


if __name__ == "__main__":
    unittest.main()
