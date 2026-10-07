from recurrence_detector import *
def e(d,src,origin="",asset="A",p="P"):return RecurrenceEvent(p,"buyer",asset,d,src,origin)
def test_single_event_not_recurrence():assert recurrence_state((e("2026-03-01","S1"),),"P","A")=="SINGLE_EVENT"
def test_duplicate_origin_not_recurrence():assert recurrence_state((e("2025-03-01","S1","O"),e("2026-03-01","S2","O")),"P","A")=="DUPLICATE_EVIDENCE"
def test_same_year_is_not_cycle():assert recurrence_state((e("2026-03-01","S1"),e("2026-08-01","S2")),"P","A")=="REPEATED_SAME_PERIOD"
def test_multi_year_independent_pattern():assert recurrence_state((e("2025-03-01","S1"),e("2026-03-01","S2")),"P","A")=="MULTI_PERIOD_PATTERN"
def test_pattern_never_claims_next_purchase():assert not may_predict_next_purchase((e("2025-03-01","S1"),e("2026-03-01","S2")),"P","A")
