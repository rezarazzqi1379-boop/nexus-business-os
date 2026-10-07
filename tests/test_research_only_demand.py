from research_only_demand import *
def row(**k):
 d=dict(buyer="B",evidence_type="SHIPMENT",source_locator="s",observed_at="2026-01-29",geometry="Ø400x6m",product="42CrMo4",current_open=False);d.update(k);return DemandEvidence(**d)
def test_historical_shipment_never_becomes_open_demand():
 x=row()
 assert research_state(x)=="HISTORICAL_OR_OBSERVED_SIGNAL"
 assert conversion_state(x,current_stock=True,technical_fit=True,relationship=True)=="RESEARCH_ONLY_CURRENTNESS_UNPROVEN"
def test_seller_page_is_not_buyer_side_demand():
 assert research_state(row(evidence_type="SELLER_CATALOG"))=="REJECT_NON_BUYER_SIDE_EVIDENCE"
def test_open_demand_without_current_stock_stays_research_only():
 assert conversion_state(row(evidence_type="RFQ",current_open=True),current_stock=False,technical_fit=True,relationship=True)=="RESEARCH_ONLY_AWAIT_STOCK"
