"""Admission plan for external GitHub capabilities. External code is sandbox-only until accepted."""
from dataclasses import dataclass
from enum import Enum

class Admission(str,Enum):
 MERGE_NATIVE="MERGE_NATIVE"; SANDBOX="SANDBOX"; DEFER="DEFER"; REJECT="REJECT"

@dataclass(frozen=True)
class Candidate:
 repo:str; purpose:str; admission:Admission; network:bool=False; models:bool=False
 untrusted_input:bool=False; acceptance_test:str=""; rollback:str="remove adapter and dependency"

def candidates()->tuple[Candidate,...]:
 return (
  Candidate("open-contracting/standard","procurement lifecycle semantics",Admission.MERGE_NATIVE,
   acceptance_test="tender->award->contract->implementation->amendment preserves lineage"),
  Candidate("open-contracting/ocdskit","OCDS validation/merge benchmark",Admission.SANDBOX,
   untrusted_input=True,acceptance_test="compile sample releases without changing NEXUS authority"),
  Candidate("docling-project/docling","procurement attachment parsing",Admission.SANDBOX,
   models=True,untrusted_input=True,acceptance_test="real attachment -> structured text/table -> content hash -> evidence bundle"),
  Candidate("PaddlePaddle/PaddleOCR","scanned/Cyrillic OCR fallback",Admission.SANDBOX,
   models=True,untrusted_input=True,acceptance_test="scanned sample improves extraction over native parser without silent field invention"),
  Candidate("moj-analytical-services/splink","multilingual legal-entity candidate generation",Admission.SANDBOX,
   acceptance_test="alias benchmark reports precision and false-merge rate; never auto-merges consequential entities"),
  Candidate("dgtlmoon/changedetection.io","web change monitoring benchmark",Admission.DEFER,
   network=True,untrusted_input=True,acceptance_test="beats native change detector on meaningful-change precision without duplicate alerts"),
 )

def may_run_in_production(c:Candidate)->bool:
 return False

def requires_sandbox(c:Candidate)->bool:
 return c.admission==Admission.SANDBOX or c.network or c.models or c.untrusted_input

def install_order()->tuple[str,...]:
 return ("open-contracting/standard","docling-project/docling","moj-analytical-services/splink","PaddlePaddle/PaddleOCR","open-contracting/ocdskit")
