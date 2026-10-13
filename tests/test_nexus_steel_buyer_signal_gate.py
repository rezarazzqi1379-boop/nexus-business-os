"""Tests for dated, sourced steel buyer signals."""
import unittest
from datetime import date
from dataclasses import replace
from nexus_steel_buyer_signal_gate import BuyerSignal, classify_signal


class BuyerSignalGateTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 13)
        self.signal = BuyerSignal("PRJ-STEEL-SALES", "Example Buyer",
                                  "https://example.org/tender/123", "BUY_TENDER", "2026-10-12")

    def test_expired_tender_is_not_active(self):
        self.assertEqual(classify_signal(self.signal, today=self.today), "BUY_TENDER_EXPIRED")

    def test_today_deadline_does_not_claim_open(self):
        s = replace(self.signal, deadline="2026-10-13")
        self.assertEqual(classify_signal(s, today=self.today), "BUY_TENDER_OPEN_STATUS_UNVERIFIED")

    def test_future_deadline_still_unverified(self):
        s = replace(self.signal, deadline="2026-11-01")
        self.assertEqual(classify_signal(s, today=self.today), "BUY_TENDER_OPEN_STATUS_UNVERIFIED")

    def test_missing_deadline_is_unknown(self):
        self.assertEqual(classify_signal(replace(self.signal, deadline=""), today=self.today),
                         "BUY_TENDER_DEADLINE_UNKNOWN")

    def test_sale_tender_is_not_buyer(self):
        self.assertEqual(classify_signal(replace(self.signal, evidence_type="SALE_TENDER"),
                                         today=self.today), "SALE_TENDER")

    def test_award_is_not_active_tender(self):
        self.assertEqual(classify_signal(replace(self.signal, evidence_type="AWARD"),
                                         today=self.today), "AWARD")

    def test_invalid_sources_and_evidence_fail_closed(self):
        for update in ({"source_url": ""}, {"source_url": "not-a-url"},
                       {"buyer_name": ""}, {"evidence_type": "CONFIRMED_BUYER"},
                       {"deadline": "tomorrow"}):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    classify_signal(replace(self.signal, **update), today=self.today)


if __name__ == "__main__":
    unittest.main()
