"""Restorable context ledger: compact pointers, never memory authority."""
from dataclasses import dataclass
@dataclass(frozen=True)
class LedgerEntry:
 project_id:str; checkpoint_id:str; git_sha:str; summary:str
 evidence_refs:tuple[str,...]; ci_run:str=""; ci_state:str=""
def valid_entry(e:LedgerEntry)->bool:
 return bool(e.project_id and e.checkpoint_id and len(e.git_sha)>=7 and e.summary and e.evidence_refs)
def resumable(e:LedgerEntry,current_project:str,current_head:str)->bool:
 return valid_entry(e) and e.project_id==current_project and e.git_sha==current_head and e.ci_state=="SUCCESS" and bool(e.ci_run)
def memory_authorizes(_:LedgerEntry)->bool:
 return False
def rehydrate_request(e:LedgerEntry,path:str="")->dict:
 if not valid_entry(e): raise ValueError("invalid_ledger_entry")
 return {"project_id":e.project_id,"git_sha":e.git_sha,"path":path,"verify_after_rehydrate":True}
