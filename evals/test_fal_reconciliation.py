from __future__ import annotations

import unittest

import fal_vertical
import prj_fal_01
from fal_reconciliation import (
    FALReconciliationError, SOURCE_VERSION_DISPUTED, UNKNOWN,
    assert_same_reconciled_scope, from_prj_binding, from_vertical_lane, reconciled_lane,
)


class ReconciliationTests(unittest.TestCase):
    def test_both_apis_converge_without_collapsing_role_dimensions(self):
        for primary, vertical in ((prj_fal_01.FAL_A, fal_vertical.FAL_A),
                                  (prj_fal_01.FAL_B, fal_vertical.FAL_B)):
            left = from_prj_binding(primary)
            right = from_vertical_lane(vertical)
            self.assertEqual(left.lane_id, right.lane_id)
            self.assertEqual(left.home_roles, right.home_roles)
            self.assertNotEqual(left.home_roles.operational, left.home_roles.economic)

    def test_dynamic_facts_accept_only_unknown_or_disputed(self):
        reconciled_lane("FAL-A", dynamic_facts={"price": UNKNOWN, "grade": SOURCE_VERSION_DISPUTED})
        with self.assertRaisesRegex(FALReconciliationError, "dynamic_fact"):
            reconciled_lane("FAL-A", dynamic_facts={"price": "123"})

    def test_cross_lane_join_fails_closed(self):
        with self.assertRaisesRegex(FALReconciliationError, "cross_lane_contamination"):
            assert_same_reconciled_scope(reconciled_lane("FAL-A"), reconciled_lane("FAL-B"))

    def test_adapter_rejects_mutated_semantics(self):
        bad = fal_vertical.FALVerticalLane(fal_vertical.PROJECT_ID, "FAL-A", "IMPORT",
            "ferromanganese", "IRAN", "PRODUCER", "SUPPLIER", "RESEARCH_UNKNOWN")
        with self.assertRaisesRegex(FALReconciliationError, "vertical_lane_semantic_mismatch"):
            from_vertical_lane(bad)


if __name__ == "__main__":
    unittest.main()
