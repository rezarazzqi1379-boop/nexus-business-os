"""Executable held-out Red Team v6 attacks against existing NEXUS controls."""
from datetime import date
from evidence_triangulation import EvidenceRef,triangulate
from discovery_coverage import evaluate_market_coverage,REQUIRED_MARKET_LAYERS
from steel_evidence_quality import evidence_freshness
from steel_trade_hs import assess_alloy_bar_hs
from held_out_red_team_fixtures import evaluate_outcomes
from commercial_integrity_guards import PriceObservation,price_comparability,grade_equivalence,entity_merge_decision
from steel_country_leads import validate_lead

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
 # role/channel separation
 lead={"lead_id":"x","country":"Germany","company":"Trader X","role":"IMPORTER","channel":"TRADER","applications":[],"grade_candidates":[],"evidence":[],"status":"CANDIDATE"}
 errs=validate_lead(lead)
 out["rt-role-001"]=("do_not_classify_as_manufacturer_without_production_evidence",("test:steel_country_leads",)) if "invalid_role" not in errs and "invalid_channel" not in errs else ("bad",("test:steel_country_leads",))
 # price comparability
 q=PriceObservation("bar","42CrMo4","300mm","forged",20,"FOB","USD","t","OFFICIAL_QUOTE")
 u=PriceObservation("bar","42CrMo4","300mm","forged",None,"FOB","USD","t","CUSTOMS_UNIT_VALUE")
 out["rt-price-001"]=("mark_not_directly_comparable",("test:commercial_integrity_guards",)) if price_comparability(q,u)=="NOT_DIRECTLY_COMPARABLE" else ("bad",("test:commercial_integrity_guards",))
 # grade equivalence
 eq=grade_equivalence(standard_a="EN",standard_b="GOST",chemistry_compared=True,mechanicals_compared=False,heat_treatment_compared=False,delivery_condition_compared=True,mtc_evidence=False)
 out["rt-eq-001"]=("remain_candidate_equivalence",("test:commercial_integrity_guards",)) if eq=="CANDIDATE_EQUIVALENCE" else ("bad",("test:commercial_integrity_guards",))
 # entity resolution
 er=entity_merge_decision(canonical_domain_same=False,legal_identifier_same=False,alias_only=True,subsidiary_possible=False)
 out["rt-entity-001"]=("require_resolution_before_dedup_merge",("test:commercial_integrity_guards",)) if er=="REQUIRE_RESOLUTION" else ("bad",("test:commercial_integrity_guards",))
 return evaluate_outcomes(out)
