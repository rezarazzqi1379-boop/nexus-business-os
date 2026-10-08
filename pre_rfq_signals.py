"""Pre-RFQ commercial signals with dual-time and source-independence semantics."""
from dataclasses import dataclass
from enum import Enum
from datetime import date

class SignalType(str,Enum):
 PROCUREMENT_PLAN="PROCUREMENT_PLAN"; CAPEX="CAPEX"; EXPANSION="EXPANSION"; SUPPLIER_QUALIFICATION="SUPPLIER_QUALIFICATION"; PROCUREMENT_HIRING="PROCUREMENT_HIRING"; ENGINEERING_HIRING="ENGINEERING_HIRING"; MAINTENANCE="MAINTENANCE"; TENDER="TENDER"; AWARD="AWARD"; SUPPLIER_CHANGE="SUPPLIER_CHANGE"

@dataclass(frozen=True)
class PreRFQSignal:
 signal_id:str; project_id:str; entity_id:str; signal_type:SignalType; source_locator:str
 observed_on:date; valid_from:date|None=None; valid_to:date|None=None
 authority:str="SECONDARY"; current:bool=False; source_origin:str=""

def valid_signal(s:PreRFQSignal,as_of:date|None=None)->bool:
 if not all((s.signal_id,s.project_id,s.entity_id,s.source_locator)): return False
 if s.valid_to and s.valid_from and s.valid_to<s.valid_from: return False
 if s.valid_from and s.valid_from>s.observed_on and s.signal_type not in {SignalType.PROCUREMENT_PLAN,SignalType.TENDER}: return False
 if as_of and s.valid_to and s.valid_to<as_of: return False
 return True

def _current(signals,as_of):
 return [s for s in signals if valid_signal(s,as_of) and s.current]

def independent_origins(signals:tuple[PreRFQSignal,...],as_of:date|None=None)->int:
 return len({s.source_origin or s.source_locator for s in _current(signals,as_of)})

def cluster_strength(signals:tuple[PreRFQSignal,...],as_of:date|None=None)->int:
 good=_current(signals,as_of); types={s.signal_type for s in good}
 score=min(60,len(types)*15)
 if SignalType.PROCUREMENT_PLAN in types: score+=20
 if SignalType.TENDER in types: score+=15
 if SignalType.AWARD in types: score+=5
 if len(good)>1 and independent_origins(signals,as_of)<2: score=min(score,25)
 return min(100,score)

def pre_rfq_candidate(signals:tuple[PreRFQSignal,...],as_of:date|None=None)->bool:
 good=_current(signals,as_of)
 early={SignalType.PROCUREMENT_PLAN,SignalType.CAPEX,SignalType.EXPANSION,SignalType.SUPPLIER_QUALIFICATION,SignalType.PROCUREMENT_HIRING,SignalType.ENGINEERING_HIRING,SignalType.MAINTENANCE,SignalType.SUPPLIER_CHANGE}
 return bool({s.signal_type for s in good}&early)
