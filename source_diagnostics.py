"""Source diagnostics: health, question-fit and bounded negative evidence."""
from dataclasses import dataclass
from enum import Enum
from commercial_source_registry import CommercialSource,SourceRole,may_support_current_procurement,may_support_verified_winner

class SourceHealth(str,Enum):
 HEALTHY="HEALTHY"; CHANGED_SCHEMA="CHANGED_SCHEMA"; EMPTY_ANOMALY="EMPTY_ANOMALY"
 AUTH_REQUIRED="AUTH_REQUIRED"; RATE_LIMITED="RATE_LIMITED"; UNREACHABLE="UNREACHABLE"
 STALE="STALE"; UNKNOWN="UNKNOWN"

class EvidenceQuestion(str,Enum):
 CURRENT_PROCUREMENT="CURRENT_PROCUREMENT"; VERIFIED_WINNER="VERIFIED_WINNER"
 MARKET_TRADE="MARKET_TRADE"; SUPPLIER_ROUTE="SUPPLIER_ROUTE"; INSTALLED_BASE="INSTALLED_BASE"

@dataclass(frozen=True)
class SourceProbe:
 source_id:str; health:SourceHealth; observed_at:str
 expected_records:int|None=None; returned_records:int|None=None; detail:str=""

def question_fit(source:CommercialSource,q:EvidenceQuestion)->bool:
 if q==EvidenceQuestion.CURRENT_PROCUREMENT:return may_support_current_procurement(source)
 if q==EvidenceQuestion.VERIFIED_WINNER:return may_support_verified_winner(source)
 if q==EvidenceQuestion.MARKET_TRADE:return source.role==SourceRole.TRADE_STATISTICS
 if q==EvidenceQuestion.SUPPLIER_ROUTE:return source.role==SourceRole.SUPPLIER_ROUTE
 if q==EvidenceQuestion.INSTALLED_BASE:return source.role==SourceRole.OEM_INSTALLED_BASE
 return False

def empty_result_is_search_evidence(probe:SourceProbe)->bool:
 """An empty result is usable only when the source itself is healthy."""
 return probe.health==SourceHealth.HEALTHY and probe.returned_records==0

def negative_evidence_statement(source:CommercialSource,probe:SourceProbe,q:EvidenceQuestion,query_scope:str)->str:
 if not question_fit(source,q):return "SOURCE_NOT_FIT_FOR_QUESTION"
 if not empty_result_is_search_evidence(probe):return "UNKNOWN_SOURCE_HEALTH_OR_NONEMPTY"
 return f"NO_MATCH_FOUND_IN_SEARCHED_SOURCE:{source.source_id}:{query_scope}"

def may_conclude_nonexistence(_:str)->bool:
 """Bounded search failure never proves global non-existence."""
 return False

def source_health_blocks_promotion(probe:SourceProbe)->bool:
 return probe.health!=SourceHealth.HEALTHY
