"""Held-out adversarial fixtures for Red Team Max v6.

Fixtures describe traps independently of implementation modules. A fixture is
not a PASS until an evaluator records evidence that the expected rejection or
classification occurred.
"""
from dataclasses import dataclass

FAMILIES=("ROLE","SOURCE","TIME","TRADE","PRICE","EQUIVALENCE","ENTITY","COVERAGE","PROVIDER")
@dataclass(frozen=True)
class Fixture:
 fixture_id:str; family:str; trap:str; expected:str
 def validate(self):
  if not self.fixture_id.strip() or self.family not in FAMILIES or not self.trap.strip() or not self.expected.strip():
   raise ValueError("invalid_fixture")

HELD_OUT=(
 Fixture("rt-role-001","ROLE","trader sells mill product","do_not_classify_as_manufacturer_without_production_evidence"),
 Fixture("rt-source-001","SOURCE","two URLs copy same upstream source","count_as_one_source_family"),
 Fixture("rt-time-001","TIME","old inventory page appears current","classify_stock_as_stale_without_fresh_observation"),
 Fixture("rt-trade-001","TRADE","country imports HS candidate","do_not_infer_named_company_buyer"),
 Fixture("rt-price-001","PRICE","customs unit value compared with executable quote","mark_not_directly_comparable"),
 Fixture("rt-eq-001","EQUIVALENCE","similar grade names across standards","remain_candidate_equivalence"),
 Fixture("rt-entity-001","ENTITY","alias and subsidiary names overlap","require_resolution_before_dedup_merge"),
 Fixture("rt-coverage-001","COVERAGE","provider unavailable for importer lane","source_unavailable_not_negative_evidence"),
 Fixture("rt-provider-001","PROVIDER","auth/rate failure returns no records","provider_failure_not_market_absence"),
)

def registry():
 for x in HELD_OUT:x.validate()
 return HELD_OUT

def evaluate_outcomes(outcomes:dict[str,tuple[str,tuple[str,...]]])->dict:
 """outcomes maps fixture_id -> (observed_classification, evidence_refs)."""
 expected={x.fixture_id:x for x in registry()}
 passed=[];failed=[];not_run=[]
 for fid,f in expected.items():
  if fid not in outcomes:not_run.append(fid);continue
  observed,refs=outcomes[fid]
  if not refs:failed.append(fid)
  elif observed==f.expected:passed.append(fid)
  else:failed.append(fid)
 return {"passed":tuple(passed),"failed":tuple(failed),"not_run":tuple(not_run),
         "complete":not failed and not not_run}
