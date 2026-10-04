import tempfile
import unittest
from pathlib import Path

from claim_state import ClaimRecord, ClaimStateStore
from engineering_sanity import Quantity, compare, validate_model


class VNextClaimAndSanityTests(unittest.TestCase):
    def test_supersession_deactivates_prior_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ClaimStateStore(Path(tmp) / "claims.db")
            store.add(ClaimRecord("c1", "PRJ-HYD-01", "supplier_price", "238461.55 USD", "gmail:m1", "CLAIM"))
            store.add(ClaimRecord("c2", "PRJ-HYD-01", "supplier_price", "240000 USD", "gmail:m2", "CLAIM", "c1"))
            active = store.active_for("PRJ-HYD-01", "supplier_price")
            self.assertEqual([row["claim_id"] for row in active], ["c2"])

    def test_cross_project_supersession_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ClaimStateStore(Path(tmp) / "claims.db")
            store.add(ClaimRecord("c1", "PRJ-HYD-01", "supplier_price", "1", "gmail:m1", "CLAIM"))
            with self.assertRaisesRegex(ValueError, "cross_project_supersession_rejected"):
                store.add(ClaimRecord("c2", "PRJ-KCL-01", "supplier_price", "2", "gmail:m2", "CLAIM", "c1"))

    def test_cross_topic_supersession_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ClaimStateStore(Path(tmp) / "claims.db")
            store.add(ClaimRecord("c1", "PRJ-HYD-01", "throughput", "60 per_hour", "gmail:m1", "CLAIM"))
            with self.assertRaisesRegex(ValueError, "cross_topic_supersession_rejected"):
                store.add(ClaimRecord("c2", "PRJ-HYD-01", "pressure", "120 MPa", "gmail:m2", "CLAIM", "c1"))

    def test_second_supersession_of_inactive_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ClaimStateStore(Path(tmp) / "claims.db")
            store.add(ClaimRecord("c1", "PRJ-HYD-01", "pressure", "120 MPa", "gmail:m1", "CLAIM"))
            store.add(ClaimRecord("c2", "PRJ-HYD-01", "pressure", "110 MPa", "gmail:m2", "CLAIM", "c1"))
            with self.assertRaisesRegex(ValueError, "superseded_claim_not_active"):
                store.add(ClaimRecord("c3", "PRJ-HYD-01", "pressure", "100 MPa", "gmail:m3", "CLAIM", "c1"))

    def test_pressure_unit_conversion_is_explicit(self):
        self.assertTrue(compare(Quantity(1200, "bar", "pressure"), Quantity(120, "MPa", "pressure")))
        self.assertFalse(compare(Quantity(1000, "bar", "pressure"), Quantity(120, "MPa", "pressure")))

    def test_rate_conversion_distinguishes_per_minute_and_per_hour(self):
        self.assertTrue(compare(Quantity(1, "per_minute", "rate"), Quantity(60, "per_hour", "rate")))
        self.assertFalse(compare(Quantity(1, "per_hour", "rate"), Quantity(60, "per_hour", "rate")))

    def test_dimension_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "quantity_dimension_mismatch"):
            compare(Quantity(120, "MPa", "pressure"), Quantity(120, "mm", "length"))

    def test_unknown_unit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported_unit"):
            compare(Quantity(120, "kg", "pressure"), Quantity(120, "MPa", "pressure"))

    def test_model_identifier_requires_exact_normalized_match(self):
        self.assertTrue(validate_model(" GSY-180 ", "gsy-180"))
        self.assertFalse(validate_model("GSY-180", "GT3B64-NFBS-5"))


if __name__ == "__main__":
    unittest.main()
