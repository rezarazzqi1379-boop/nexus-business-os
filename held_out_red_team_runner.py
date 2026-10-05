"""Executable held-out Red Team v6 attacks against existing NEXUS controls."""
from datetime import date
from evidence_triangulation import EvidenceRef,triangulate
from discovery_coverage import evaluate_market_coverage,REQUIRED_MARKET_LAYERS
from steel_evidence_quality import evidence_freshness
from steel_trade_hs import assess_alloy_bar_hs
from held_out_red_team_fixtures import evaluate_outcomes

def run_existing_controls()->dict:
 out={}
 # copied sources
 t=triangulate((EvidenceRef("a","OFFICIAL_COMPANY","same"),EvidenceRef("b","INDEPENDENT_SOURCE","same")))
 out["rt-source-001"]=("count_as_one_source_family",("test:evidence_triangulation",)) if t["independent_sources"]==1 else ("bad",("test:evidence_triangulation",))
 # stale stock
 fr=evidence_freshness("2025-01-01",max_age_days=180,today=date(2026,10,5))
 out["rt-time-001"]=("classify_stock_as_stale_without_fresh_observation",("test:evidence_freshness",)) if fr=="STALE" else ("bad",("test:evidence_freshness",))
 # trade candidate remains non-company attribution: HS helper only returns candidate family and blockers
 hs=assess_alloy_bar_hs(alloy_steel=True,bar_or_rod=True,condition="forged",further_worked=False)
 out["rt-trade-001"]=("do_not_infer_named_company_buyer",("test:steel_trade_hs",)) if hs.candidate_heading=="722840" and hs.blockers else ("bad",("test:steel_trade_hs",))
 # coverage/provider outage
 s={x:"COVERED" for x in REQUIRED_MARKET_LAYERS};s["IMPORTER"]="SOURCE_UNAVAILABLE"
 cov=evaluate_market_coverage(s)
 expected="source_unavailable_not_negative_evidence"
 out["rt-coverage-001"]=(expected,("test:discovery_coverage",)) if "IMPORTER" in cov["blind"] and not cov["complete"] else ("bad",("test:discovery_coverage",))
 out["rt-provider-001"]=("provider_failure_not_market_absence",("test:discovery_coverage",)) if "IMPORTER" in cov["blind"] else ("bad",("test:discovery_coverage",))
 return evaluate_outcomes(out)
