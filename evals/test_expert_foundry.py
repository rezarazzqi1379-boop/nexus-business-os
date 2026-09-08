from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from expert_foundry import (
    ConversationRecord,
    ExperienceRecord,
    ExpertFoundryStore,
    HypothesisRecord,
    KnowledgeRecord,
    PromotionDecision,
    ResearchTrace,
)


NOW = "2026-09-08T00:00:00+00:00"


def knowledge(record_type: str = "CLAIM", **changes) -> KnowledgeRecord:
    base = KnowledgeRecord(
        record_id="knowledge_001", record_type=record_type, domain="metallurgy",
        title="Observed relationship", statement="A bounded observation",
        source_class="PRIMARY_RESEARCH", source_locator="doi:10.example/test",
        captured_at=NOW, confidence=0.4,
        project_id="project_fal",
        operating_context="furnace-2; bounded heat window" if record_type == "EXPERIENCE" else "",
    )
    return replace(base, **changes)


class KnowledgeContractTests(unittest.TestCase):
    def test_claim_is_valid_but_unverified(self):
        knowledge().validate()

    def test_experience_requires_context(self):
        with self.assertRaisesRegex(ValueError, "experience_requires_operating_context"):
            knowledge("EXPERIENCE", operating_context="").validate()

    def test_raw_source_cannot_arrive_preverified(self):
        with self.assertRaisesRegex(ValueError, "raw_source_cannot_arrive_preverified"):
            knowledge("SOURCE", verification_state="CORROBORATED").validate()

    def test_promotion_requires_support(self):
        with self.assertRaisesRegex(ValueError, "promoted_state_requires_store_transition"):
            knowledge(maturity_state="PROMOTED").validate()

    def test_contradictions_are_preserved_and_deduplicated(self):
        knowledge(contradiction_refs=("claim_a", "claim_b")).validate()
        with self.assertRaisesRegex(ValueError, "duplicate_contradiction_ref"):
            knowledge(contradiction_refs=("claim_a", "claim_a")).validate()

    def test_experience_wrapper_requires_validation_plan(self):
        item = ExperienceRecord(knowledge("EXPERIENCE"), "operator", 3, "lower defect rate", "", False)
        with self.assertRaisesRegex(ValueError, "invalid_experience_detail"):
            item.validate()


class HypothesisAndPromotionTests(unittest.TestCase):
    def test_hypothesis_requires_grounding(self):
        item = HypothesisRecord("hypothesis_1", "metallurgy", "defect", "mechanism", "change",
                                "controlled test", (), (), ("alternative",), NOW, "project_fal")
        with self.assertRaisesRegex(ValueError, "hypothesis_requires_grounding"):
            item.validate()

    def test_hypothesis_requires_alternative_explanations(self):
        item = HypothesisRecord("hypothesis_1", "metallurgy", "defect", "mechanism", "change",
                                "controlled test", ("claim_a",), (), (), NOW, "project_fal")
        with self.assertRaisesRegex(ValueError, "hypothesis_requires_alternatives"):
            item.validate()

    def test_ai_cannot_promote_without_human_approval(self):
        item = PromotionDecision("decision_1", "knowledge_001", "PROMOTE", "codex",
                                 ("claim_a",), "eval_1", NOW, "supported", "project_fal")
        with self.assertRaisesRegex(ValueError, "promotion_requires_human_approval"):
            item.validate()

    def test_hold_does_not_require_approval(self):
        PromotionDecision("decision_1", "knowledge_001", "HOLD", "claude",
                          (), "eval_1", NOW, "insufficient evidence", "project_fal").validate()

    def test_research_trace_preserves_exact_query(self):
        ResearchTrace("run_1", "bounded review", ("exact query",), ("provider_1",),
                      ("source_1",), ("source_2",), ("gap_1",), NOW, NOW,
                      "diminishing returns", "project_fal").validate()

    def test_research_trace_cannot_hide_missing_query(self):
        item = ResearchTrace("run_1", "bounded review", (), ("provider_1",), (), (), (),
                             NOW, NOW, "no query", "project_fal")
        with self.assertRaisesRegex(ValueError, "research_trace_requires_query"):
            item.validate()

    def test_conversation_is_never_authority(self):
        item = ConversationRecord("conversation_1", "chat", ("user", "assistant"),
                                  "chat:conversation_1", NOW, (), "0" * 64,
                                  "project_fal", None, "CANONICAL")
        with self.assertRaisesRegex(ValueError, "conversation_cannot_be_authority"):
            item.validate()


class StoreTests(unittest.TestCase):
    def test_append_and_verify_hash_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ExpertFoundryStore(Path(temp))
            store.append(knowledge())
            store.append(ResearchTrace("run_1", "bounded review", ("query",), ("provider_1",),
                                       (), (), (), NOW, NOW, "complete", "project_fal"))
            self.assertTrue(store.verify_chain())

    def test_experience_record_is_stored_with_details(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ExpertFoundryStore(Path(temp))
            item = ExperienceRecord(knowledge("EXPERIENCE"), "operator", 3,
                                    "lower defect rate", "controlled trial", True)
            store.append(item)
            self.assertIn("validation_plan", store.events_path.read_text())

    def test_promotion_requires_decision_and_same_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ExpertFoundryStore(Path(temp))
            supported = knowledge(verification_state="CORROBORATED")
            decision = PromotionDecision("decision_1", supported.record_id, "PROMOTE", "human",
                                         ("claim_a",), "eval_1", NOW, "supported",
                                         "other_project", None, "approval_1")
            with self.assertRaisesRegex(ValueError, "cross_scope_promotion"):
                store.promote(supported, decision)

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ExpertFoundryStore(Path(temp))
            store.append(knowledge())
            store.events_path.write_text(store.events_path.read_text().replace("bounded", "tampered"))
            self.assertFalse(store.verify_chain())

    def test_snapshot_is_digest_bound_and_non_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ExpertFoundryStore(Path(temp))
            store.append(knowledge())
            snapshot = store.create_snapshot("snapshot_001")
            self.assertEqual(json.loads(snapshot.read_text())["snapshot_id"], "snapshot_001")
            with self.assertRaises(FileExistsError):
                store.create_snapshot("snapshot_001")


if __name__ == "__main__":
    unittest.main()
