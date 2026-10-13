"""Pre-filter procurement evidence against stock geometry before expensive qualification."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DemandGeometry:
 grade:str; form:str; diameter_mm:float|None; length_m:float|None
def geometry_route(d:DemandGeometry, *, stock_grade:str, stock_form:str, dmin:float,dmax:float,lmin:float,lmax:float)->str:
 if d.grade.casefold()!=stock_grade.casefold(): return "REJECT_GRADE"
 if d.form.casefold()!=stock_form.casefold(): return "REJECT_FORM"
 if d.diameter_mm is None or d.length_m is None: return "FOLLOWUP_MISSING_GEOMETRY"
 if not dmin<=d.diameter_mm<=dmax: return "REJECT_DIAMETER"
 if not lmin<=d.length_m<=lmax: return "REJECT_LENGTH"
 return "QUALIFY_TECHNICAL"
