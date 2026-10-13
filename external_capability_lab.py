"""Vendor-neutral External Capability Lab.

Patterns are reverse-engineered from public systems, but admission remains governed
by NEXUS evidence, acceptance, sandbox and ablation gates. No external runtime is
trusted or activated by this module.
"""
from dataclasses import dataclass
from enum import Enum

class LabDecision(str,Enum):
    REJECT="REJECT"; STUDY="STUDY"; SANDBOX="SANDBOX"; ABLATE="ABLATE"; PROMOTE_PATTERN="PROMOTE_PATTERN"

@dataclass(frozen=True)
class ExternalPattern:
    pattern_id:str
    evidence_refs:tuple[str,...]
    acceptance_tests:tuple[str,...]
    deterministic:bool
    external_runtime_required:bool
    secrets_required:bool=False
    external_write:bool=False
    known_failure_refs:tuple[str,...]=()

def lab_decision(p:ExternalPattern, *, measured_bottleneck:bool, sandbox_passed:bool=False, ablation_win:bool=False)->LabDecision:
    if not p.pattern_id or not p.evidence_refs or not p.acceptance_tests:
        return LabDecision.REJECT
    if not measured_bottleneck:
        return LabDecision.STUDY
    if p.secrets_required or p.external_write or p.external_runtime_required:
        if not sandbox_passed:
            return LabDecision.SANDBOX
    if not sandbox_passed:
        return LabDecision.SANDBOX
    if not ablation_win:
        return LabDecision.ABLATE
    return LabDecision.PROMOTE_PATTERN

@dataclass(frozen=True)
class ExtractionProof:
    snapshot_ref:str
    selector_ref:str
    validation_ref:str
    structured_rows:int
    source_locator:str

def extraction_evidence_ready(p:ExtractionProof)->bool:
    return bool(p.snapshot_ref and p.selector_ref and p.validation_ref and p.source_locator and p.structured_rows>0)

@dataclass(frozen=True)
class EvaluationProof:
    trajectory_checked:bool
    tool_selection_checked:bool
    failure_diagnosis_checked:bool
    deterministic_fault_tested:bool

def evaluation_pattern_ready(p:EvaluationProof)->bool:
    return all((p.trajectory_checked,p.tool_selection_checked,p.failure_diagnosis_checked,p.deterministic_fault_tested))
