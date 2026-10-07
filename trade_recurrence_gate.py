"""Deduplicate trade observations before recurrence claims."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TradeObservation:
 buyer:str; date:str; hs:str; weight_kg:str; product_fingerprint:str
def observation_key(o:TradeObservation)->tuple[str,...]:
 return tuple(x.strip().casefold() for x in (o.buyer,o.date,o.hs,o.weight_kg,o.product_fingerprint))
def independent_observations(rows):
 return tuple({observation_key(r):r for r in rows}.values())
def recurrence_state(rows)->str:
 return "RECURRENT" if len(independent_observations(rows))>=2 else "ONE_OBSERVED"
