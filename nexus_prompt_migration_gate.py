"""Regression policy gate for NEXUS v14 candidate prompt migration.

Pure deterministic checks; no access to local Windows, billing or external actions.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class MigrationScenario:
    dirty_local_tree: bool = False
    canonical_sources_available: bool = True
    project_scope_matches: bool = True
    exact_head_ci_green: bool = True
    paid_action_requested: bool = False
    exact_paid_approval: bool = False
    outbound_requested: bool = False
    exact_outbound_approval: bool = False
    global_activation_claimed_without_readback: bool = False

def migration_gate(s: MigrationScenario) -> tuple[bool, tuple[str, ...]]:
    blocks = []
    if s.dirty_local_tree:
        blocks.append("local_mutation_blocked")
    if not s.canonical_sources_available:
        blocks.append("canonical_authority_missing")
    if not s.project_scope_matches:
        blocks.append("cross_project_evidence_blocked")
    if not s.exact_head_ci_green:
        blocks.append("red_or_unknown_ci")
    if s.paid_action_requested and not s.exact_paid_approval:
        blocks.append("unapproved_paid_action")
    if s.outbound_requested and not s.exact_outbound_approval:
        blocks.append("unapproved_outbound")
    if s.global_activation_claimed_without_readback:
        blocks.append("unverified_global_activation")
    return not blocks, tuple(blocks)
