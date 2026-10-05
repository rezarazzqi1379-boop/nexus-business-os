"""Read-only change-set health for NEXUS v7."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ChangeSet:
 commits:int; files_changed:int; contracts_changed:int=0; schemas_changed:int=0; modules_touched:int=0
 def validate(self):
  if any(type(x) is not int or x<0 for x in (self.commits,self.files_changed,self.contracts_changed,self.schemas_changed,self.modules_touched)):
   raise ValueError("invalid_change_set")

def assess(x:ChangeSet)->dict:
 x.validate()
 score=0; reasons=[]
 for hit,pts,msg in (
  (x.commits>100,2,"very_large_commit_count"),
  (x.files_changed>60,2,"very_large_file_surface"),
  (x.contracts_changed>2,1,"multiple_contract_changes"),
  (x.schemas_changed>0,1,"schema_migration_surface"),
  (x.modules_touched>30,1,"broad_module_surface")):
  if hit:score+=pts;reasons.append(msg)
 level="HIGH" if score>=4 else "MEDIUM" if score>=2 else "LOW"
 return {"risk":level,"score":score,"reasons":tuple(reasons),
         "recommendation":"split_or_freeze_scope" if level=="HIGH" else "preserve_small_reversible_commits"}
