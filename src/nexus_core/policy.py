from dataclasses import dataclass
from typing import Literal
from unicodedata import category


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
_MAX_ACTION_ID_LENGTH = 256
_MAX_DESCRIPTION_LENGTH = 1024
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


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


def _compact_text_error(
    field_name: str,
    value: object,
    *,
    max_length: int,
) -> str | None:
    """Return one fail-closed validation error for control-plane text metadata."""

    if not isinstance(value, str):
        return f"{field_name} must be a string"
    if not value.strip():
        return f"{field_name} is required"
    if value != value.strip():
        return f"{field_name} cannot have leading or trailing whitespace"
    if len(value) > max_length:
        return f"{field_name} must be at most {max_length} characters"
    if any(category(character) in _DISALLOWED_UNICODE_CATEGORIES for character in value):
        return f"{field_name} cannot contain control or formatting characters"
    return None


def _approval_error(approval: ActionApproval | None) -> str | None:
    if approval is None:
        return None
    if not isinstance(approval, ActionApproval):
        return "approval must be an ActionApproval"
    action_id_error = _compact_text_error(
        "approval.action_id",
        approval.action_id,
        max_length=_MAX_ACTION_ID_LENGTH,
    )
    if action_id_error:
        return action_id_error
    if not isinstance(approval.approved, bool):
        return "approval.approved must be a boolean"
    return None


def _has_matching_approval(intent: ActionIntent, approval: ActionApproval | None) -> bool:
    return bool(
        isinstance(approval, ActionApproval)
        and approval.approved is True
        and isinstance(approval.action_id, str)
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
    signature, contract/PO or destructive action. Runtime inputs are validated fail-closed
    because dataclass type hints do not enforce types at runtime.
    """
    if not isinstance(intent, ActionIntent):
        return GateDecision(False, False, "intent must be an ActionIntent")

    action_id_error = _compact_text_error(
        "action_id",
        intent.action_id,
        max_length=_MAX_ACTION_ID_LENGTH,
    )
    if action_id_error:
        return GateDecision(False, False, action_id_error)

    description_error = _compact_text_error(
        "description",
        intent.description,
        max_length=_MAX_DESCRIPTION_LENGTH,
    )
    if description_error:
        return GateDecision(False, False, description_error)

    if not isinstance(intent.kind, str):
        return GateDecision(False, False, "kind must be a string")
    if intent.kind not in _ALLOWED_ACTION_KINDS:
        return GateDecision(False, False, "unsupported action kind")
    if not isinstance(intent.reversible, bool):
        return GateDecision(False, False, "reversible must be a boolean")

    approval_error = _approval_error(approval)
    if approval_error:
        return GateDecision(False, intent.kind in _HUMAN_GATED or not intent.reversible, approval_error)

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
