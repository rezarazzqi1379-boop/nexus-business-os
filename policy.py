from __future__ import annotations

from dataclasses import dataclass


READ_ONLY_ACTIONS = frozenset({"read", "classify", "research", "compare", "draft", "test", "summarize"})
REVERSIBLE_LOCAL_ACTIONS = frozenset({
    "local_edit", "sandbox_experiment", "record_evidence", "local_backup",
})
EXTERNAL_ACTIONS = frozenset({
    "send", "reply", "forward", "publish", "merge", "deploy", "pay", "contract",
    "permission_change", "database_write", "create_account", "accept_terms", "submit_kyc",
    "link_payment", "enable_paid_plan",
})


@dataclass(frozen=True)
class PolicyDecision:
    disposition: str
    reason: str


def decide_action(action: str, *, approved: bool = False) -> PolicyDecision:
    normalized = action.strip().lower()
    if normalized in READ_ONLY_ACTIONS:
        return PolicyDecision("allow", "read_only_or_reversible")
    if normalized in REVERSIBLE_LOCAL_ACTIONS:
        return PolicyDecision("allow", "owner_delegated_reversible_local_action")
    if normalized in EXTERNAL_ACTIONS:
        if approved:
            return PolicyDecision("allow_once", "explicit_human_approval")
        return PolicyDecision("approval_required", "external_or_high_impact_action")
    return PolicyDecision("deny", "unknown_capability_fails_closed")

