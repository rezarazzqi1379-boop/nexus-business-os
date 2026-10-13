"""Transparent evidence quality ranking. Scores never authorize commercial action."""
from dataclasses import dataclass
from enum import Enum

class AuthorityLevel(str,Enum):
 PRIMARY="PRIMARY"; OFFICIAL_SECONDARY="OFFICIAL_SECONDARY"; RELIABLE_SECONDARY="RELIABLE_SECONDARY"; DISCOVERY="DISCOVERY"; UNKNOWN="UNKNOWN"
class EvidenceFreshness(str,Enum):
 CURRENT="CURRENT"; RECENT="RECENT"; HISTORICAL="HISTORICAL"; STALE="STALE"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class QualityEvidence:
 evidence_id:str; project_id:str; origin_root:str; authority:AuthorityLevel
 freshness:EvidenceFreshness; direct:bool=False; contradicted:bool=False

_AUTH={AuthorityLevel.PRIMARY:1.0,AuthorityLevel.OFFICIAL_SECONDARY:.85,AuthorityLevel.RELIABLE_SECONDARY:.65,AuthorityLevel.DISCOVERY:.30,AuthorityLevel.UNKNOWN:.10}
_FRESH={EvidenceFreshness.CURRENT:1.0,EvidenceFreshness.RECENT:.80,EvidenceFreshness.HISTORICAL:.45,EvidenceFreshness.STALE:.10,EvidenceFreshness.UNKNOWN:.20}

def evidence_weight(e:QualityEvidence)->float:
 if not e.evidence_id or not e.project_id or not e.origin_root or e.contradicted:return 0.0
 direct=1.0 if e.direct else .8
 return round(_AUTH[e.authority]*_FRESH[e.freshness]*direct,4)

def independent_quality(evidence:tuple[QualityEvidence,...],project_id:str)->float:
 """One best item per origin root prevents copied evidence from inflating quality."""
 best:dict[str,float]={}
 for e in evidence:
  if e.project_id!=project_id:continue
  root=e.origin_root.strip().lower()
  if not root:continue
  best[root]=max(best.get(root,0.0),evidence_weight(e))
 return round(sum(best.values()),4)

def quality_band(score:float)->str:
 if score>=2.0:return "STRONG_MULTI_ORIGIN"
 if score>=1.0:return "SUPPORTED"
 if score>0:return "WEAK"
 return "NONE"

def may_authorize_action(_:float)->bool:
 """A score is a triage aid, never action authority."""
 return False
