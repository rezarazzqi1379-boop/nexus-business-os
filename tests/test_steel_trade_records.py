from steel_trade_records import TradeQuery,TradeResult,validate_trade_result
def test_trade_result_requires_provenance_and_measurement():
 q=TradeQuery("Turkey","World","722840","IMPORT","2025")
 r=TradeResult(q,"UN Comtrade","2026-10-05",trade_value_usd=1,source_ref="comtrade:query")
 assert validate_trade_result(r)==()
def test_claim_without_source_ref_fails():
 q=TradeQuery("Turkey","World","722840","IMPORT","2025")
 r=TradeResult(q,"aggregator","2026-10-05",trade_value_usd=1)
 assert "source_ref_required" in validate_trade_result(r)
def test_negative_measurement_fails():
 q=TradeQuery("Turkey","World","722840","IMPORT","2025")
 r=TradeResult(q,"UN Comtrade","2026-10-05",net_weight_kg=-1,source_ref="x")
 assert "negative:net_weight_kg" in validate_trade_result(r)
