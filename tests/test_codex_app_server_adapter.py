import unittest

from nexus_core.codex_app_server_adapter import ObservationPhase, normalize_app_server_event


DIGEST = "a" * 64


def observe(method: str):
    return normalize_app_server_event(
        {"id": "evt-1", "method": method},
        project_id="PRJ-HYD-01",
        packet_digest=DIGEST,
    )


class CodexAppServerAdapterTests(unittest.TestCase):
    def test_completed_means_produced_never_accepted(self):
        result = observe("turn/completed")
        self.assertIs(result.phase, ObservationPhase.PRODUCED)
        self.assertEqual(result.reason, "runner_turn_completed_unverified")
        self.assertNotIn("accepted", {phase.value for phase in ObservationPhase})

    def test_approval_and_input_events_fail_closed(self):
        for method in (
            "item/commandExecution/requestApproval",
            "item/fileChange/requestApproval",
            "item/tool/requestUserInput",
        ):
            with self.subTest(method=method):
                result = observe(method)
                self.assertIs(result.phase, ObservationPhase.BLOCKED)
                self.assertEqual(result.reason, "exact_human_input_or_approval_required")

    def test_unknown_event_fails_closed(self):
        result = observe("experimental/newEvent")
        self.assertIs(result.phase, ObservationPhase.BLOCKED)
        self.assertEqual(result.reason, "unknown_app_server_event")

    def test_project_and_packet_binding_are_preserved(self):
        result = observe("turn/started")
        self.assertEqual(result.project_id, "PRJ-HYD-01")
        self.assertEqual(result.packet_digest, DIGEST)
        self.assertEqual(result.observation_id, "codex-app-server:evt-1")

    def test_invalid_packet_digest_is_rejected(self):
        for digest in ("", "A" * 64, "x" * 64, "a" * 63):
            with self.subTest(digest=digest):
                with self.assertRaisesRegex(ValueError, "packet_digest"):
                    normalize_app_server_event(
                        {"id": "evt-1", "method": "turn/started"},
                        project_id="PRJ-HYD-01",
                        packet_digest=digest,
                    )


if __name__ == "__main__":
    unittest.main()
