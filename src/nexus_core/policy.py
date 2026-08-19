from dataclasses import dataclass
from typing import Literal


ActionKind = Literal[
    "read",
    "research",
    "draft",
    "branch_commit",
    "internal_record_write",
    "send_external_message",
    "merge_code",
    "production_deploy",
    "change_access",
    "delete_or_archive",
    "contract_or_po",
    "payment",
    "signature",
]

_ALLOWED_ACTION_KINDS = {
    "read",
    "research",
    "draft",
    "branch_commit",
    "internal_record_write",
    "send_external_message",
    "merge_code",
    "production_deploy",
    "change_access",
    "delete_or_archive",
    "contract_or_po",
    "payment",
    "signature",
}
_HUMAN_GATED = {
    "send_external_message",
    "merge_code",
    "production_deploy",
    "change_access",
    "delete_or_archive",
    "contract_or_po",
    "payment",
    "signature",
}


@dataclass(frozen=True)
class ActionIntent:
    action_id: str
    kind: ActionKind
    description: str
    reversible: bool = True


@dataclass(frozen=True)
class ActionApproval:
    action_id: str
    approved: bool = True


@dataclass(frozen=True)
class GateDecision:
    allowed_now: bool
    requires_human_approval: bool
    reason: str


def _has_matching_approval(intent: ActionIntent, approval: ActionApproval | None) -> bool:
    return bool(
        approval is not None
        and approval.approved
        and approval.action_id.strip()
        and approval.action_id == intent.action_id
    )


def evaluate_action(
    intent: ActionIntent,
    *,
    approval: ActionApproval | None = None,
) -> GateDecision:
    """Apply NEXUS consequential-action gates.

    Approval is deliberately action-scoped. A generic or earlier blanket approval must
    not silently authorize an unrelated future payment, send, deploy, permission change,
    signature, contract/PO or destructive action.
    """
    if not intent.action_id.strip():
        return GateDecision(False, False, "action_id is required")
    if not intent.description.strip():
        return GateDecision(False, False, "description is required")
    if intent.kind not in _ALLOWED_ACTION_KINDS:
        return GateDecision(False, False, "unsupported action kind")

    matched_approval = _has_matching_approval(intent, approval)

    if intent.kind in _HUMAN_GATED:
        if matched_approval:
            return GateDecision(True, False, "matching human approval recorded")
        return GateDecision(
            False,
            True,
            f"{intent.kind} requires approval for action_id={intent.action_id}",
        )

    if not intent.reversible:
        if matched_approval:
            return GateDecision(True, False, "matching human approval recorded")
        return GateDecision(
            False,
            True,
            "non-reversible action requires action-specific human approval",
        )

    return GateDecision(True, False, "low-risk or reversible internal action")
