from pathlib import Path
from steel_trade_hub_adapter import ingest_trade_result
from steel_trade_records import TradeQuery,TradeResult
from unified_data_environment import UnifiedDataHub
def test_trade_ingest_is_idempotent(tmp_path):
 hub=UnifiedDataHub(tmp_path/"hub.sqlite",tmp_path)
 q=TradeQuery("Turkey","World","722840","IMPORT","2025")
 r=TradeResult(q,"UN Comtrade","2026-10-05T00:00:00+00:00",trade_value_usd=12,source_ref="comtrade:q1")
 assert ingest_trade_result(hub,r) is True
 assert ingest_trade_result(hub,r) is False
 assert len(hub.project_view("STEEL_SALES"))==1
def test_invalid_trade_result_never_reaches_hub(tmp_path):
 hub=UnifiedDataHub(tmp_path/"hub.sqlite",tmp_path)
 q=TradeQuery("Turkey","World","bad","IMPORT","2025")
 r=TradeResult(q,"UN Comtrade","2026-10-05T00:00:00+00:00",trade_value_usd=12,source_ref="x")
 try: ingest_trade_result(hub,r); assert False
 except ValueError as e: assert "invalid_trade_result" in str(e)
