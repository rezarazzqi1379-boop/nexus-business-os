import json
import unittest
from dataclasses import replace

from commercial_relationship_proof import RelationshipReview, prove_relationship
from incremental_intelligence import Observation
from steel_commercial_intelligence import EvidenceKind, IntelEdge, current_demand_ready

NOW = "2026-10-13T00:00:00+00:00"


def fixture():
    # Deliberately fictional companies/documents; no live sales claim.
    body = json.dumps(dict(buyer_id="buyer-fixture", legal_id="TEST-123",
                           product_id="forged-shaft", relation="CURRENT_RFQ")).encode()
    observations = tuple(Observation("SANDBOX", "commercial-proof", f"fixture://source/{i}",
                                     f"publisher-{i}", NOW, body, "structured-v1") for i in range(2))
    reviews = tuple(RelationshipReview(o.project_id, o.lane, o.source_ref, o.digest,
                                      o.origin_id, "buyer-fixture", "TEST-123", "forged-shaft",
                                      "CURRENT_RFQ", NOW, "2026-10-20T00:00:00+00:00",
                                      "fixture-reviewer") for o in observations)
    return observations, reviews


def run(observations=None, reviews=None, **changes):
    default_observations, default_reviews = fixture()
    args = dict(project_id="SANDBOX", lane="commercial-proof", buyer_id="buyer-fixture",
                product_id="forged-shaft", legal_identities={"buyer-fixture": "TEST-123"},
                reviews=default_reviews if reviews is None else reviews, as_of=NOW)
    args.update(changes)
    return prove_relationship(default_observations if observations is None else observations, **args)


class CommercialProofTests(unittest.TestCase):
    def test_source_to_reviewed_graph_and_commercial_gate(self):
        result = run()
        self.assertTrue(result.ready_for_research)
        self.assertEqual([e.state for e in result.graph], ["VERIFIED", "VERIFIED"])
        self.assertTrue(all("sha256=" in e.source_id for e in result.graph))
        self.assertEqual(result.model_tokens, 0)

    def test_false_entity_name_or_legal_id(self):
        observations, reviews = fixture()
        body = observations[0].payload.replace(b"TEST-123", b"TEST-124")
        altered = tuple(replace(o, payload=body) for o in observations)
        self.assertFalse(run(altered, reviews).ready_for_research)
        self.assertIn("entity_or_product_mismatch", run(altered, reviews).rejection_reasons)

    def test_source_cannot_self_certify(self):
        self.assertFalse(run(reviews=()).ready_for_research)

    def test_changed_payload_invalidates_review(self):
        observations, reviews = fixture()
        altered = tuple(replace(o, payload=o.payload + b" ") for o in observations)
        self.assertFalse(run(altered, reviews).ready_for_research)

    def test_stale_and_future_source(self):
        observations, reviews = fixture()
        for date in ("2025-01-01T00:00:00+00:00", "2027-01-01T00:00:00+00:00"):
            self.assertFalse(run(tuple(replace(o, observed_at=date) for o in observations), reviews).ready_for_research)

    def test_duplicate_ingestion_and_repeat(self):
        observations, reviews = fixture()
        first = run(observations + observations, reviews)
        repeat = run(history=first.history)
        self.assertEqual(len(first.history), 2)
        self.assertEqual(repeat.history, first.history)
        self.assertEqual(len(first.graph), 2)

    def test_cache_hit_does_not_extend_expired_review(self):
        first = run()
        self.assertFalse(run(history=first.history, as_of="2026-10-21T00:00:00+00:00").ready_for_research)

    def test_cross_project_and_lane_rejected_atomically(self):
        observations, reviews = fixture()
        for changes in (dict(project_id="OTHER"), dict(lane="OTHER")):
            with self.assertRaisesRegex(ValueError, "cross_scope"):
                run((observations[0], replace(observations[1], **changes)), reviews)

    def test_review_cannot_cross_scope(self):
        observations, reviews = fixture()
        self.assertFalse(run(observations, tuple(replace(r, lane="OTHER") for r in reviews)).ready_for_research)

    def test_conflicting_revision_cannot_count_as_corroboration(self):
        observations, reviews = fixture()
        with self.assertRaisesRegex(ValueError, "conflicting_batch_revision"):
            run((observations[0], replace(observations[0], origin_id="other")), reviews)

    def test_mirrors_not_independent(self):
        observations, reviews = fixture()
        observations = tuple(replace(o, origin_id="publisher-0") for o in observations)
        reviews = tuple(replace(r, origin_id="publisher-0") for r in reviews)
        self.assertFalse(run(observations, reviews).ready_for_research)

    def test_unauthorized_actions_blocked_even_with_verified_relationship(self):
        for action in ("send", "pay", "merge", "deploy", "database_write", "unknown"):
            with self.assertRaisesRegex(ValueError, "research_only"):
                run(action=action)

    def test_unrelated_evidence_cannot_satisfy_existing_gate(self):
        edges = tuple(IntelEdge("SANDBOX", left, rel, right, ref, NOW, EvidenceKind.OBSERVED, True)
                      for left, rel, right, ref in (
                          ("buyer-fixture", "USES", "unrelated", "A"),
                          ("stranger", "CURRENT_RFQ", "forged-shaft", "B")))
        self.assertFalse(current_demand_ready(edges, "SANDBOX", "buyer-fixture", "forged-shaft"))

    def test_budget_rejects_before_ingestion(self):
        with self.assertRaisesRegex(ValueError, "budget"):
            run(max_bytes=1)

    def test_malformed_claim_and_naive_time_fail_closed(self):
        observations, reviews = fixture()
        self.assertFalse(run(tuple(replace(o, payload=b"[]") for o in observations), reviews).ready_for_research)
        with self.assertRaisesRegex(ValueError, "timezone"):
            run(as_of="2026-10-13")


if __name__ == "__main__":
    unittest.main()
