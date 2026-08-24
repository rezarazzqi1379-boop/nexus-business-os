import json
import unittest
from pathlib import Path

from entry_map import load_entry_map


DATA = Path(__file__).parents[1] / "data" / "entry_map_baku_eastpipes_2026-08-21.json"


class EntryMapTests(unittest.TestCase):
    def test_fact_hypothesis_unknown_are_separate(self):
        opportunities = load_entry_map(DATA)
        self.assertEqual(len(opportunities), 5)
        self.assertTrue(all(item.fact != item.hypothesis for item in opportunities))
        self.assertTrue(all(item.unknowns for item in opportunities))

    def test_expired_and_completed_packages_are_not_actionable(self):
        opportunities = load_entry_map(DATA)
        by_id = {item.opportunity_id: item for item in opportunities}
        self.assertFalse(by_id["baku-straightener-foundation-031"].is_actionable)
        self.assertFalse(by_id["east-hsaw-line-2025"].is_actionable)

    def test_only_verified_open_package_is_actionable(self):
        opportunities = load_entry_map(DATA)
        actionable = [item.opportunity_id for item in opportunities if item.is_actionable]
        self.assertEqual(actionable, ["east-coating-line-2026"])

    def test_outreach_remains_blocked(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertFalse(payload["outreach_authorized"])


if __name__ == "__main__":
    unittest.main()
