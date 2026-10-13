"""Versioned NEXUS Prompt OS registry and fail-closed router."""
from dataclasses import dataclass
from enum import Enum

class PromptLayer(str,Enum):
 KERNEL="KERNEL"; CAPABILITY="CAPABILITY"; ADAPTER="ADAPTER"; PROJECT="PROJECT"; EVAL="EVAL"

@dataclass(frozen=True)
class PromptSpec:
 prompt_id:str; version:str; layer:PromptLayer; purpose:str
 acceptance_test:str; rollback_to:str=""; active:bool=False

@dataclass(frozen=True)
class PromptRequest:
 project_id:str; capability:str; adapter:str=""; protected_action:bool=False
 dynamic_fact_required:bool=False; live_evidence_refreshed:bool=False

def valid_prompt(p:PromptSpec)->bool:
 return bool(p.prompt_id and p.version and p.purpose and p.acceptance_test)

def may_activate(p:PromptSpec,test_green:bool,measured_improvement:bool)->bool:
 return valid_prompt(p) and test_green and measured_improvement

def route_prompt(r:PromptRequest)->tuple[str,...]:
 if not r.project_id or not r.capability: raise ValueError("missing_prompt_scope")
 if r.dynamic_fact_required and not r.live_evidence_refreshed:
  raise ValueError("refresh_dynamic_evidence")
 layers=["NEXUS_KERNEL"]
 layers.append(f"CAPABILITY:{r.capability}")
 if r.adapter: layers.append(f"ADAPTER:{r.adapter}")
 layers.append(f"PROJECT:{r.project_id}")
 layers.append("EVAL:SELF_CHECK")
 if r.protected_action: layers.append("GATE:HUMAN_APPROVAL")
 return tuple(layers)

def prompt_may_embed_dynamic_fact()->bool:
 return False
