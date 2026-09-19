from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from canonical_sources import CanonicalStore, hydrostatic_hold_points
from contracts import EvidenceClass
from engineering_review import PRJ_HYD_01, SupplierEvidenceSnapshot, review_supplier_evidence

ROOT = Path(__file__).resolve().parents[1]


def supplier(**changes) -> SupplierEvidenceSnapshot:
    values = dict(
        project_id=PRJ_HYD_01,
        source_ref="gmail:message:1a03db0ec7ca5dfd",
        supplier_name="GH",
        received_at="2026-08-30T00:00:00+00:00",
        statement="Thank you for the enquiry.",
        evidence_classification=EvidenceClass.CLAIM,
    )
    values.update(changes)
    return SupplierEvidenceSnapshot(**values)


class EngineeringReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = CanonicalStore(Path(self.temp.name) / "canonical.db")
        self.store.ingest_directory(ROOT / "canonical_source_files")

    def tearDown(self):
        self.temp.cleanup()

    def _deltas_by_code(self, result: dict) -> dict:
        return {item["code"]: item for item in result["deltas"]}

    def test_confirmed_disposition_with_matching_excerpts(self):
        statement = ("We confirm 120 MPa test pressure, a signed capability matrix, "
                     "and closure of FAT/TPI/ITP acceptance, at 60 pipes/hour.")
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        deltas = self._deltas_by_code(result)
        for code in ("HYD-PRESSURE", "HYD-THROUGHPUT", "HYD-CAPABILITY-MATRIX", "HYD-FAT"):
            self.assertEqual(deltas[code]["supplier_disposition"], "CONFIRMED")
            self.assertTrue(deltas[code]["buyer_requirement_excerpt"])
            self.assertTrue(deltas[code]["supplier_evidence_excerpt"])

    def test_contradicted_disposition_with_matching_excerpts(self):
        statement = ("Our tester is only rated to 80 MPa and runs at 45 pipes/hour. "
                     "We are unable to provide a capability matrix and will not provide FAT/TPI/ITP.")
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        deltas = self._deltas_by_code(result)
        for code in ("HYD-PRESSURE", "HYD-THROUGHPUT", "HYD-CAPABILITY-MATRIX", "HYD-FAT"):
            self.assertEqual(deltas[code]["supplier_disposition"], "CONTRADICTED")
            self.assertTrue(deltas[code]["buyer_requirement_excerpt"])
            self.assertTrue(deltas[code]["supplier_evidence_excerpt"])

    def test_silent_disposition_when_topic_is_not_addressed(self):
        statement = "Our delivery lead time is 12 weeks and payment terms are 30% advance."
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        deltas = self._deltas_by_code(result)
        for code in ("HYD-PRESSURE", "HYD-THROUGHPUT", "HYD-CAPABILITY-MATRIX", "HYD-FAT"):
            self.assertEqual(deltas[code]["supplier_disposition"], "SILENT")

    def test_silent_fabricates_no_supplier_excerpt(self):
        statement = "Our delivery lead time is 12 weeks."
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        for delta in result["deltas"]:
            if delta["supplier_disposition"] == "SILENT":
                self.assertIsNone(delta["supplier_evidence_excerpt"])

    def test_confirmed_requires_supplier_excerpt(self):
        statement = "We confirm 120 MPa test pressure."
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        pressure = self._deltas_by_code(result)["HYD-PRESSURE"]
        self.assertEqual(pressure["supplier_disposition"], "CONFIRMED")
        self.assertTrue(pressure["supplier_evidence_excerpt"])

    def test_contradicted_requires_supplier_excerpt(self):
        statement = "Our tester is only rated to 80 MPa."
        result = review_supplier_evidence(self.store, supplier(statement=statement))
        pressure = self._deltas_by_code(result)["HYD-PRESSURE"]
        self.assertEqual(pressure["supplier_disposition"], "CONTRADICTED")
        self.assertTrue(pressure["supplier_evidence_excerpt"])

    def test_source_bound_prj_hyd_01_lookup(self):
        result = review_supplier_evidence(self.store, supplier())
        self.assertEqual(result["project_id"], PRJ_HYD_01)
        self.assertEqual(result["buyer_source_id"], "PRJ-HYD-01-ENG")

    def test_missing_canonical_source_fails_closed(self):
        empty_store = CanonicalStore(Path(self.temp.name) / "empty.db")
        with self.assertRaises(KeyError):
            review_supplier_evidence(empty_store, supplier())

    def test_no_cross_project_fallback(self):
        with self.assertRaisesRegex(ValueError, "engineering_review_scoped_to_prj_hyd_01"):
            review_supplier_evidence(self.store, supplier(project_id="PRJ-CAN-01"))

    def test_external_action_authorized_is_always_false(self):
        for statement in (
            "We confirm 120 MPa test pressure.",
            "Our tester is only rated to 80 MPa.",
            "Our delivery lead time is 12 weeks.",
        ):
            result = review_supplier_evidence(self.store, supplier(statement=statement))
            self.assertFalse(result["external_action_authorized"])

    def test_identical_input_yields_identical_digest(self):
        first = review_supplier_evidence(self.store, supplier())
        second = review_supplier_evidence(self.store, supplier())
        self.assertEqual(first["report_digest"], second["report_digest"])
        changed = review_supplier_evidence(self.store, supplier(statement="We confirm 120 MPa test pressure."))
        self.assertNotEqual(first["report_digest"], changed["report_digest"])

    def test_supplier_name_does_not_affect_disposition_or_isolation(self):
        statement = "We confirm 120 MPa test pressure."
        a = review_supplier_evidence(self.store, supplier(statement=statement, supplier_name="GH"))
        b = review_supplier_evidence(self.store, supplier(statement=statement, supplier_name="Marley"))
        deltas_a = self._deltas_by_code(a)["HYD-PRESSURE"]
        deltas_b = self._deltas_by_code(b)["HYD-PRESSURE"]
        self.assertEqual(deltas_a["supplier_disposition"], deltas_b["supplier_disposition"])

    def test_evidence_classification_is_never_promoted_to_fact(self):
        result = review_supplier_evidence(self.store, supplier(
            statement="We confirm 120 MPa test pressure.",
            evidence_classification=EvidenceClass.CLAIM,
        ))
        self.assertEqual(result["supplier_evidence_classification"], "CLAIM")

    def test_invalid_evidence_classification_fails_closed(self):
        with self.assertRaises(ValueError):
            supplier(evidence_classification="NOT_A_REAL_CLASS").validate()

    def test_no_mutation_of_canonical_db(self):
        before = self.store.status()
        review_supplier_evidence(self.store, supplier(statement="We confirm 120 MPa test pressure."))
        after = self.store.status()
        self.assertEqual(before, after)

    def test_hydrostatic_hold_points_behavior_is_unchanged(self):
        result = hydrostatic_hold_points(self.store)
        self.assertEqual(result["source_id"], "PRJ-HYD-01-ENG")
        self.assertFalse(result["external_action_authorized"])
        self.assertEqual({item["code"] for item in result["findings"]},
                         {"HYD-PRESSURE", "HYD-THROUGHPUT", "HYD-CAPABILITY-MATRIX", "HYD-FAT"})


if __name__ == "__main__":
    unittest.main()
