"""Compare fresh auditable stock evidence with historical snapshots without overwriting history."""
from dataclasses import dataclass
from stock_evidence_contract import stock_evidence_state
@dataclass(frozen=True)
class SnapshotRow:
 grade:str; diameter:str; length:str; tonnage:float
def delta_state(old:SnapshotRow, fresh:dict)->str:
 if stock_evidence_state(fresh)!="CURRENT_STOCK_EVIDENCED": return "UNKNOWN_INCOMPLETE_FRESH_EVIDENCE"
 if str(fresh["grade"]).casefold()!=old.grade.casefold(): return "DIFFERENT_GRADE"
 same_geometry=(str(fresh["diameter"]).strip()==old.diameter and str(fresh["length"]).strip()==old.length)
 if not same_geometry: return "CHANGED_GEOMETRY"
 new=float(fresh["tonnage"])
 if new==old.tonnage: return "AVAILABLE_CONFIRMED_UNCHANGED"
 if new<old.tonnage: return "AVAILABLE_CONFIRMED_DECREASED"
 return "AVAILABLE_CONFIRMED_INCREASED"
