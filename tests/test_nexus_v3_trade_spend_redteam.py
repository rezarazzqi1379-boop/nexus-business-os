from steel_trade_records import TradeQuery,TradeResult
from steel_trade_hub_adapter import CONFIDENCE
from apollo_spend_gate import assess_spend
def test_commercial_trade_source_never_gets_official_confidence():
 assert CONFIDENCE["COMMERCIAL_AGGREGATOR"]<CONFIDENCE["TRADE_DATASET"]<CONFIDENCE["OFFICIAL_CUSTOMS"]
def test_trade_source_type_is_explicit():
 r=TradeResult(TradeQuery("TR","IR","722840","IMPORT","2025"),"vendor","2026-10-05T00:00:00+00:00",source_type="COMMERCIAL_AGGREGATOR",trade_value_usd=1,source_ref="v:1")
 assert r.source_type=="COMMERCIAL_AGGREGATOR"
def test_apollo_spend_boolean_claims_without_refs_are_blocked():
 d=assess_spend(buyer_fit=90,evidence_current=True,dedup_clear=True,free_resolution_attempted=True,existing_contact=False,expected_value=True)
 assert not d.eligible
 assert {"current_evidence_ref_required","free_resolution_ref_required","commercial_value_ref_required"}<=set(d.blockers)
def test_apollo_spend_with_refs_is_eligible_not_authorized():
 d=assess_spend(buyer_fit=90,evidence_current=True,dedup_clear=True,free_resolution_attempted=True,existing_contact=False,expected_value=True,evidence_refs=("e:1",),free_resolution_refs=("apollo-free:1",),value_refs=("value:1",))
 assert d.eligible
