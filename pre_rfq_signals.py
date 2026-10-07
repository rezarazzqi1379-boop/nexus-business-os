"""Pre-RFQ commercial signals with dual-time evidence semantics."""
from dataclasses import dataclass
from enum import Enum
from datetime import date

class SignalType(str,Enum):
 PROCUREMENT_PLAN="PROCUREMENT_PLAN"; CAPEX="CAPEX"; EXPANSION="EXPANSION"; SUPPLIER_QUALIFICATION="SUPPLIER_QUALIFICATION"; PROCUREMENT_HIRING="PROCUREMENT_HIRING"; ENGINEERING_HIRING="ENGINEERING_HIRING"; MAINTENANCE="MAINTENANCE"; TENDER="TENDER"; AWARD="AWARD"; SUPPLIER_CHANGE="SUPPLIER_CHANGE"

@dataclass(frozen=True)
class PreRFQSignal:
 signal_id:str
 project_id:str
 entity_id:str
 signal_type:SignalType
 source_locator:str
 observed_on:date
 valid_from:date|None=None
 valid_to:date|None=None
 authority:str="SECONDARY"
 current:bool=False

def valid_signal(s:PreRFQSignal)->bool:
 if not all((s.signal_id,s.project_id,s.entity_id,s.source_locator)): return False
 if s.valid_from and s.valid_from>s.observed_on and s.signal_type not in {SignalType.PROCUREMENT_PLAN,SignalType.TENDER}: return False
 return True

def cluster_strength(signals:tuple[PreRFQSignal,...])->int:
 good=[s for s in signals if valid_signal(s) and s.current]
 types={s.signal_type for s in good}
 score=min(60,len(types)*15)
 if SignalType.PROCUREMENT_PLAN in types: score+=20
 if SignalType.TENDER in types: score+=15
 if SignalType.AWARD in types: score+=5
 return min(100,score)

def pre_rfq_candidate(signals:tuple[PreRFQSignal,...])->bool:
 current={s.signal_type for s in signals if valid_signal(s) and s.current}
 early={SignalType.PROCUREMENT_PLAN,SignalType.CAPEX,SignalType.EXPANSION,SignalType.SUPPLIER_QUALIFICATION,SignalType.PROCUREMENT_HIRING,SignalType.ENGINEERING_HIRING,SignalType.MAINTENANCE,SignalType.SUPPLIER_CHANGE}
 return bool(current & early)
