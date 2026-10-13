"""Evidence-safe stock matching: a dimensional/grade match is not a current-stock promise."""
from dataclasses import dataclass
@dataclass(frozen=True)
class StockLot:
 grade:str; dmin:float; dmax:float; lmin:float; lmax:float; tonnes:float; currentness:str="UNKNOWN"
def dimensional_match(lot:StockLot,grade:str,diameter:float,length:float)->bool:
 return lot.grade.casefold()==grade.casefold() and lot.dmin<=diameter<=lot.dmax and lot.lmin<=length<=lot.lmax
def match_state(lot:StockLot,grade:str,diameter:float,length:float)->str:
 if not dimensional_match(lot,grade,diameter,length): return "NO_MATCH"
 return "CURRENT_STOCK_MATCH" if lot.currentness=="CURRENT" else "SNAPSHOT_MATCH_RECONFIRM_STOCK"
def can_quote_as_available(lot:StockLot)->bool:
 return lot.currentness=="CURRENT"
