from stock_evidence_contract import *
def test_snapshot_is_not_complete_stock_evidence():
 r={"grade":"42CrMo4","diameter":"290-760","length":"2-7","tonnage":"80"}
 assert stock_evidence_state(r)=="INCOMPLETE_STOCK_EVIDENCE"
 assert "observed_at" in missing_stock_fields(r)
def test_complete_record():
 r={k:"x" for k in REQUIRED}
 assert stock_evidence_state(r)=="CURRENT_STOCK_EVIDENCED"
