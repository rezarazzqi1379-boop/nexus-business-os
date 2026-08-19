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


@dataclass(frozen=True)
class ActionIntent:
    action_id: str
    kind: ActionKind
    description: str
    reversible: bool = True


@dataclass(frozen=True)
class GateDecision:
    allowed_now: bool
    requires_human_approval: bool
    reason: str


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


def evaluate_action(intent: ActionIntent, *, human_approved: bool = False) -> GateDecision:
    """Apply NEXUS consequential-action gates.

    Research, reads, drafts, reversible branch commits and internal evidence records may
    proceed without a separate approval. Consequential external or irreversible actions
    require an explicit human approval signal for that action.
    """
    if not intent.action_id.strip():
        return GateDecision(False, False, "action_id is required")
    if not intent.description.strip():
        return GateDecision(False, False, "description is required")

    if intent.kind in _HUMAN_GATED:
        if human_approved:
            return GateDecision(True, False, "explicit human approval recorded")
        return GateDecision(
            False,
            True,
            f"{intent.kind} is human-gated",
        )

    if not intent.reversible and intent.kind not in _HUMAN_GATED:
        return GateDecision(
            False,
            True,
            "non-reversible action requires human approval even if its kind is normally low risk",
        )

    return GateDecision(True, False, "low-risk or reversible internal action")
