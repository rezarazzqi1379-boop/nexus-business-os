"""Commercial output closure: reversible route pruning and evidence-safe opportunity output."""
from dataclasses import dataclass
from enum import Enum

class RouteState(str,Enum):
 PRIMARY="PRIMARY"; SUPPORT_ONLY="SUPPORT_ONLY"; DEPRECATED_PRIMARY="DEPRECATED_PRIMARY"; STOPPED="STOPPED"

class CommercialState(str,Enum):
 DISCOVERY="DISCOVERY"; HISTORICAL_SIGNAL="HISTORICAL_SIGNAL"; POSSIBLE_REISSUE="POSSIBLE_REISSUE"
 CURRENT_TRIGGER_VERIFIED="CURRENT_TRIGGER_VERIFIED"; AWARD_VERIFIED="AWARD_VERIFIED"; EVIDENCE_READY="EVIDENCE_READY"

@dataclass(frozen=True)
class RoutePolicy:
 route:str; state:RouteState; replacement:str=""; reason:str=""

@dataclass(frozen=True)
class CommercialOutput:
 opportunity_id:str; project_id:str; buyer:str; product_scope:str; state:CommercialState
 source_locators:tuple[str,...]; winner:str=""; current_deadline:str=""
 primary_bound:bool=False; action_authorized:bool=False

def route_policies()->tuple[RoutePolicy,...]:
 return (
  RoutePolicy("DIRECT_PROCUREMENT_AWARD",RouteState.PRIMARY),
  RoutePolicy("MERCHANT_TRADE_RELATIONSHIP",RouteState.PRIMARY),
  RoutePolicy("OEM_INSTALLED_BASE_REVERSE",RouteState.PRIMARY),
  RoutePolicy("APPLICATION_FIRST",RouteState.SUPPORT_ONLY,reason="relevance support; no measured relationship/current-trigger conversion"),
  RoutePolicy("GENERIC_WEB_PROCUREMENT",RouteState.DEPRECATED_PRIMARY,"DIRECT_PROCUREMENT_AWARD","zero measured conversion; retain only for discovery clues"),
 )

def may_promote_current(o:CommercialOutput)->bool:
 return o.primary_bound and o.state in {CommercialState.CURRENT_TRIGGER_VERIFIED,CommercialState.EVIDENCE_READY} and bool(o.current_deadline)

def may_promote_incumbent(o:CommercialOutput)->bool:
 return o.primary_bound and o.state==CommercialState.AWARD_VERIFIED and bool(o.winner)

def may_execute_external(_:CommercialOutput)->bool:
 return False

def replay_outputs()->tuple[CommercialOutput,...]:
 return (
  CommercialOutput("KZ-CHAIN-KAJSERVIS-2026","PRJ-CHAIN-SALES","KAJservis Almaty branch",
   "chain drives and connecting elements for cutter/conveyor",CommercialState.POSSIBLE_REISSUE,
   ("aggregator:goszakup-mirror:2026-09-30","mirror:possible-reissue:2026-10"),current_deadline="2026-10-12",primary_bound=False),
  CommercialOutput("KZ-MRO-ALTYNALMAS-2089730","PRJ-CHAIN-SALES","AK Altynalmas",
   "conveyor rollers",CommercialState.AWARD_VERIFIED,
   ("ets-tender:2089730",),winner="TOO KODAVARI",primary_bound=False),
 )

def commercial_snapshot()->dict:
 xs=replay_outputs()
 return {
  "outputs":len(xs),
  "primary_bound":sum(x.primary_bound for x in xs),
  "current_verified":sum(may_promote_current(x) for x in xs),
  "incumbent_verified":sum(may_promote_incumbent(x) for x in xs),
  "external_actions_authorized":0,
 }
