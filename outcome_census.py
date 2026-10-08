"""Outcome census: measure agents/routes by commercial evidence delta, not activity volume."""
from dataclasses import dataclass
from enum import Enum

class OutcomeClass(str,Enum):
 FALSE_POSITIVE_PREVENTED="FALSE_POSITIVE_PREVENTED"
 RELEVANCE_IMPROVED="RELEVANCE_IMPROVED"
 RELATIONSHIP_BOUND="RELATIONSHIP_BOUND"
 CURRENT_TRIGGER_BOUND="CURRENT_TRIGGER_BOUND"
 DECISION_MAKER_BOUND="DECISION_MAKER_BOUND"
 CONTACT_VERIFIED="CONTACT_VERIFIED"
 EVIDENCE_READY="EVIDENCE_READY"

@dataclass(frozen=True)
class RouteOutcome:
 route:str; searches:int; relationship_bound:int=0; current_trigger:int=0
 decision_maker:int=0; contact_verified:int=0; evidence_ready:int=0
 false_positives_prevented:int=0; high_information:int=0

def conversion_yield(x:RouteOutcome)->float:
 if x.searches<=0:return 0.0
 weighted=(x.relationship_bound*2+x.current_trigger*3+x.decision_maker*2+x.contact_verified*2+x.evidence_ready*5)
 return round(weighted/x.searches,4)

def guard_yield(x:RouteOutcome)->float:
 return round(x.false_positives_prevented/x.searches,4) if x.searches>0 else 0.0

def decision(x:RouteOutcome)->str:
 if x.evidence_ready>0 or x.current_trigger>0:return "EXPAND"
 if x.relationship_bound>0:return "KEEP_AND_BIND_NEXT_EDGE"
 if x.high_information>0 or x.false_positives_prevented>0:return "SUPPORT_OR_REROUTE"
 return "STOP_OR_REDESIGN"

def registered_benchmarks()->tuple[RouteOutcome,...]:
 # v10.4 + v10.5: six registered searches per route.
 return (
  RouteOutcome("MERCHANT_HUB",6,relationship_bound=2,false_positives_prevented=6,high_information=5),
  RouteOutcome("APPLICATION_FIRST",6,false_positives_prevented=6,high_information=3),
  RouteOutcome("GENERIC_WEB_PROCUREMENT",6,false_positives_prevented=6,high_information=0),
 )

def priority_routes()->tuple[str,...]:
 return ("DIRECT_PROCUREMENT_AWARD","MERCHANT_TRADE_RELATIONSHIP","OEM_INSTALLED_BASE_REVERSE")
