import unittest
from nexus_eoe_sourcing import validate_supplier, outreach_allowed

BASE = dict(project_id="PRJ-EOE-PILOT-01", source_locator="supplier/page", evidence_category="CLAIM", listing_status="ADVERTISED_UNVERIFIED", quote_status="NO_PRICE", capacity_basis="UNKNOWN")

class EvidenceGates(unittest.TestCase):
    def test_sold_not_available(self):
        self.assertIn("sold_not_available", validate_supplier({**BASE, "listing_status":"SOLD", "available":True}))
    def test_ad_price_not_formal(self):
        self.assertIn("advertisement_not_formal_quote", validate_supplier({**BASE, "quote_status":"PUBLIC_ADVERTISED_PRICE", "formal_quote":True}))
    def test_unknown_capacity_not_pass(self):
        self.assertIn("capacity_unverified", validate_supplier({**BASE, "capacity_pass":True}))
    def test_cross_project_isolation(self):
        self.assertIn("project_isolation", validate_supplier({**BASE, "project_id":"PRJ-CAN-01"}))
    def test_outreach_requires_exact_gate(self):
        self.assertFalse(outreach_allowed({"recipient":"supplier@example.com"}))
    def test_source_required(self):
        self.assertIn("missing:source_locator", validate_supplier({**BASE, "source_locator":""}))
    def test_valid_claim(self):
        self.assertEqual([], validate_supplier(BASE))

if __name__ == "__main__":
    unittest.main()
