from stock_delta import *
def fresh(**x):
 d=dict(observed_at="2026-10-07",grade="42CrMo4",standard="EN 10083-3",diameter="290-760",length="2-7",tonnage="80",condition="QT",heat_lot="H1",certificate_ref="MTC1",availability_window="2026-10-07/2026-10-14",source_owner="warehouse")
 d.update(x); return d
def test_incomplete_fresh_evidence_never_promotes_snapshot():
 old=SnapshotRow("42CrMo4","290-760","2-7",80)
 d=fresh(); d["observed_at"]=""
 assert delta_state(old,d)=="UNKNOWN_INCOMPLETE_FRESH_EVIDENCE"
def test_complete_equal_stock_confirms_without_rewriting_history():
 assert delta_state(SnapshotRow("42CrMo4","290-760","2-7",80),fresh())=="AVAILABLE_CONFIRMED_UNCHANGED"
def test_decrease_is_explicit():
 assert delta_state(SnapshotRow("42CrMo4","290-760","2-7",80),fresh(tonnage="50"))=="AVAILABLE_CONFIRMED_DECREASED"
