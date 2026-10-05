"""Durable, append-first project memory for NEXUS agents."""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

Namespace=Literal["preference","decision","context","constraint","lesson"]

@dataclass(frozen=True)
class MemoryEntry:
    entry_id:str; namespace:Namespace; statement:str; decided_by:str; created_at:str
    project_id:str|None=None; lane:str|None=None; evidence_refs:tuple[str,...]=()
    superseded_by:str|None=None
    def to_json(self)->str: return json.dumps(asdict(self),ensure_ascii=False,sort_keys=True)
    @classmethod
    def from_json(cls,s:str):
        d=json.loads(s); d["evidence_refs"]=tuple(d.get("evidence_refs",())); return cls(**d)

class ProjectMemoryStore:
    _names={"preference","decision","context","constraint","lesson"}
    def __init__(self,path:Path):
        self.path=Path(path); self.path.mkdir(parents=True,exist_ok=True)

    def _file(self,ns:str)->Path: return self.path/f"{ns}.jsonl"
    def _all(self):
        out=[]
        for ns in sorted(self._names):
            p=self._file(ns)
            if p.exists():
                for line in p.read_text(encoding="utf-8").splitlines():
                    if line.strip(): out.append(MemoryEntry.from_json(line))
        return out
    def _rewrite(self,ns:str,items):
        self._file(ns).write_text("".join(x.to_json()+"\n" for x in items),encoding="utf-8")
    def _validate(self,ns,statement,decided_by,evidence_refs):
        if ns not in self._names: raise ValueError("invalid_namespace")
        if not isinstance(statement,str) or not statement.strip(): raise ValueError("invalid_statement")
        if len(statement)>2000: raise ValueError("statement_too_long")
        if any(ord(c)<32 and c not in "\n\t" for c in statement): raise ValueError("invalid_control_characters_in_statement")
        if not isinstance(decided_by,str) or not decided_by.strip(): raise ValueError("invalid_decided_by")
        if len(evidence_refs)>20: raise ValueError("too_many_evidence_refs")
    def record(self,namespace:Namespace,statement:str,*,decided_by:str,project_id=None,lane=None,evidence_refs=(),entry_id=None):
        evidence_refs=tuple(evidence_refs); self._validate(namespace,statement,decided_by,evidence_refs)
        existing=self._all()
        if entry_id and any(x.entry_id==entry_id for x in existing): raise ValueError("duplicate_entry_id")
        if not entry_id:
            nums=[int(x.entry_id.rsplit("-",1)[1]) for x in existing if x.namespace==namespace and x.entry_id.startswith(namespace+"-") and x.entry_id.rsplit("-",1)[1].isdigit()]
            entry_id=f"{namespace}-{(max(nums,default=0)+1):04d}"
        e=MemoryEntry(entry_id,namespace,statement,decided_by,datetime.now(timezone.utc).isoformat(),project_id,lane,evidence_refs)
        with self._file(namespace).open("a",encoding="utf-8") as f:f.write(e.to_json()+"\n")
        return e
    def query(self,*,namespace=None,project_id=None,lane=None,include_superseded=True):
        items=self._all()
        if namespace is not None: items=[x for x in items if x.namespace==namespace]
        if project_id is not None: items=[x for x in items if x.project_id==project_id]
        if lane is not None: items=[x for x in items if x.lane==lane]
        if not include_superseded: items=[x for x in items if x.superseded_by is None]
        supersessions=self._supersessions()
        if supersessions:
            materialized=[]
            for x in items:
                target=supersessions.get(x.entry_id)
                if target and x.superseded_by!=target:
                    d=asdict(x); d["superseded_by"]=target; d["evidence_refs"]=tuple(d["evidence_refs"]); x=MemoryEntry(**d)
                materialized.append(x)
            items=materialized
        if not include_superseded: items=[x for x in items if x.superseded_by is None]
        return tuple(sorted(items,key=lambda x:(x.created_at,x.entry_id)))
    def supersede(self,namespace:Namespace,entry_id:str,*,superseded_by:str):
        items=list(self.query(namespace=namespace))
        if not any(x.entry_id==entry_id for x in items): raise KeyError("unknown_entry_id")
        if not any(x.entry_id==superseded_by for x in self._all()): raise KeyError("unknown_superseding_entry_id")
        event={"namespace":namespace,"entry_id":entry_id,"superseded_by":superseded_by,
               "created_at":datetime.now(timezone.utc).isoformat()}
        with self._events_file().open("a",encoding="utf-8") as f:
            f.write(json.dumps(event,ensure_ascii=False,sort_keys=True)+"\\n")
    def bootstrap_context(self,limit=20):
        if type(limit) is not int or limit<1: raise ValueError("invalid_limit")
        items=list(self.query(include_superseded=False))[-limit:]
        if not items:return "(no recorded project memory yet)"
        return "\n".join(f"[{x.namespace}/{x.entry_id}] {x.statement}"+(f" | evidence: {', '.join(x.evidence_refs)}" if x.evidence_refs else "") for x in items)
