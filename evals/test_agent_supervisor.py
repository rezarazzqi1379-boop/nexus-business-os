import unittest

from agent_supervisor import AcceptanceContract, ArtifactClaim, Phase, Supervisor, TaskRecord


def contract(**changes):
    values = dict(
        project_id="hydrotester",
        expected_packet_digest="packet-v1",
        required_tests=("pressure-boundary", "evidence-check"),
        required_evidence=("decision-pack-v1",),
        max_runtime_seconds=60,
        max_cost_units=10,
    )
    values.update(changes)
    return AcceptanceContract(**values)


def claim(**changes):
    values = dict(
        project_id="hydrotester",
        packet_digest="packet-v1",
        artifact=b"reviewed hydrotester result",
        evidence=("decision-pack-v1",),
        passed_tests=("pressure-boundary", "evidence-check"),
    )
    values.update(changes)
    return ArtifactClaim(**values)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.s = Supervisor()
        self.t = TaskRecord("hydro-001", contract())

    def produced(self):
        self.s.observe(self.t, observation_id="o1", runner_state="done", now=100)

    def test_done_is_only_produced_not_accepted(self):
        self.produced()
        self.assertEqual(self.t.phase, Phase.PRODUCED)

    def test_accepts_only_complete_bound_claim(self):
        self.produced()
        self.assertEqual(self.s.verify(self.t, claim()), Phase.ACCEPTED)

    def test_rejects_cross_project_artifact(self):
        self.produced()
        self.assertEqual(self.s.verify(self.t, claim(project_id="can-forming")), Phase.REJECTED)
        self.assertIn("cross_project_artifact", self.t.reasons)

    def test_rejects_digest_mismatch(self):
        self.produced()
        self.assertEqual(self.s.verify(self.t, claim(packet_digest="other")), Phase.REJECTED)

    def test_rejects_missing_evidence_or_tests(self):
        self.produced()
        self.s.verify(self.t, claim(evidence=(), passed_tests=()))
        self.assertIn("missing_evidence", self.t.reasons)
        self.assertIn("missing_or_failed_tests", self.t.reasons)

    def test_blocked_never_auto_answers(self):
        phase = self.s.observe(self.t, observation_id="o1", runner_state="blocked", now=100)
        self.assertEqual(phase, Phase.BLOCKED)
        self.assertIn("human_decision_required", self.t.reasons)

    def test_budget_exhaustion_fails_closed(self):
        self.s.observe(self.t, observation_id="o1", runner_state="working", now=100)
        self.assertEqual(
            self.s.observe(self.t, observation_id="o2", runner_state="working", now=161),
            Phase.FAILED,
        )

    def test_duplicate_observation_is_idempotent(self):
        self.s.observe(self.t, observation_id="same", runner_state="working", now=100, cost_delta=4)
        self.s.observe(self.t, observation_id="same", runner_state="done", now=101, cost_delta=4)
        self.assertEqual(self.t.phase, Phase.RUNNING)
        self.assertEqual(self.t.cost_units, 4)

    def test_human_approval_contract_fails_closed_without_exact_consumer(self):
        self.t = TaskRecord("hydro-002", contract(requires_human_approval=True))
        self.produced()
        self.assertEqual(self.s.verify(self.t, claim()), Phase.REJECTED)
        self.assertIn("exact_human_approval_consumer_not_implemented", self.t.reasons)

    def test_truthy_boolean_cannot_impersonate_exact_approval(self):
        self.t = TaskRecord("hydro-003", contract(requires_human_approval=True))
        self.produced()
        self.assertEqual(self.s.verify(self.t, claim(human_approved=True)), Phase.REJECTED)
        self.assertIn("exact_human_approval_consumer_not_implemented", self.t.reasons)


if __name__ == "__main__":
    unittest.main()
