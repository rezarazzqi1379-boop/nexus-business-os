"""Minimal deterministic admission checks for multi-runner platform task packets."""
from dataclasses import dataclass

PROTECTED = frozenset({"send", "publish", "pay", "sign", "order", "merge", "deploy",
                       "production_write", "external_crm_write", "paid_credit"})

@dataclass(frozen=True)
class RunnerPacket:
    task_id: str
    project_id: str
    canonical_source_refs: tuple[str, ...]
    expected_artifact: str
    evidence_requirements: tuple[str, ...]
    tests: tuple[str, ...]
    budget: int
    allowed_actions: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    rollback: str

def admission_errors(packet: RunnerPacket, *, expected_project_id: str) -> tuple[str, ...]:
    errors = []
    if not expected_project_id or packet.project_id != expected_project_id:
        errors.append("project_scope_mismatch")
    if not packet.task_id.strip() or not packet.expected_artifact.strip():
        errors.append("missing_task_or_artifact")
    if not packet.canonical_source_refs or any(not x.strip() for x in packet.canonical_source_refs):
        errors.append("canonical_sources_missing")
    if not packet.evidence_requirements or not packet.tests:
        errors.append("evidence_or_tests_missing")
    if packet.budget <= 0 or not packet.rollback.strip():
        errors.append("budget_or_rollback_missing")
    if PROTECTED.intersection(packet.allowed_actions):
        errors.append("protected_action_not_permitted")
    if set(packet.allowed_actions).intersection(packet.prohibited_actions):
        errors.append("contradictory_permissions")
    if len(set(packet.canonical_source_refs)) != len(packet.canonical_source_refs):
        errors.append("duplicate_source_refs")
    return tuple(errors)
