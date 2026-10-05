"""Discovery coverage map. Unsearched is not negative evidence."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CoverageCell:
 country:str; industry:str; application:str; product:str; buyer_type:str; source_type:str; method_id:str
 checked:bool=False; evidence_refs:tuple[str,...]=()
def blind_cells(cells):
 return tuple(c for c in cells if not c.checked)
def evidence_state(c:CoverageCell):
 if not c.checked:return "NOT_CHECKED"
 return "EVIDENCE_FOUND" if c.evidence_refs else "NO_EVIDENCE"
