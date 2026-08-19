from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Literal, Sequence

from nexus_core.policy import ActionApproval, GateDecision


CommercialActionKind = Literal[
    "discover",
    "qualify",
    "draft",
    "send_intro",
    "send_followup",
    "ask_clarification",
    "request_meeting",
    "request_quote",
    "nonbinding_negotiate",
    "prepare_deal_packet",
    "accept_offer",
    "issue_po",
    "sign_contract",
    "make_payment",
    "change_bank_details",
]

_ROUTINE_AUTONOMOUS_ACTIONS = frozenset(
    {
        "discover",
        "qualify",
        "draft",
        "send_intro",
        "send_followup",
        "ask_clarification",
        "request_meeting",
        "request_quote",
        "nonbinding_negotiate",
        "prepare_deal_packet",
    }
)
_BINDING_ACTIONS = frozenset(
    {
        "accept_offer",
        "issue_po",
        "sign_contract",
        "make_payment",
        "change_bank_details",
    }
)
_ALLOWED_CHANNELS = frozenset({"email", "linkedin", "whatsapp", "other"})
_MAX_REF = 256
_MAX_TEXT = 2048
_MAX_TARGETS = 500
_MAX_MESSAGES_PER_TARGET = 8
_MAX_MANDATE_HOURS = 24 * 31


@dataclass(frozen=True)
class CommercialMandate:
    """Human-approved boundary for autonomous, non-binding commercial work.

    The mandate is intentionally narrow: it authorizes routine outreach and negotiation
    only inside an exact project/campaign envelope. It never authorizes a binding deal,
    PO, contract, payment, signature, or bank-detail change.
    """

    mandate_id: str
    project_ref: str
    campaign_ref: str
    created_at: str
    expires_at: str
    source_version_refs: tuple[str, ...]
    allowed_channels: tuple[str, ...]
    allowed_product_refs: tuple[str, ...]
    max_targets: int = 100
    max_messages_per_target: int = 4
    allow_nonbinding_negotiation: bool = True


@dataclass(frozen=True)
class CommercialAction:
    action_id: str
    kind: CommercialActionKind
    target_ref: str
    project_ref: str
    campaign_ref: str
    channel: str | None = None
    message_ordinal: int = 0
    content_digest: str | None = None


@dataclass(frozen=True)
class MandateDecision:
    allowed_now: bool
    requires_final_deal_gate: bool
    reason: str


@dataclass(frozen=True)
class DealDecisionPacket:
    packet_id: str
    project_ref: str
    counterparty_ref: str
    source_version_refs: tuple[str, ...]
    technical_fit_refs: tuple[str, ...]
    commercial_terms_refs: tuple[str, ...]
    compliance_refs: tuple[str, ...]
    risk_refs: tuple[str, ...]
    open_issue_refs: tuple[str, ...]
    recommendation: Literal["deal", "no_deal", "conditional", "insufficient_evidence"]


@dataclass(frozen=True)
class FinalDealDecision:
    packet_id: str
    decision: Literal["deal", "no_deal"]
    gate: GateDecision


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _valid_text(value: object, max_length: int = _MAX_TEXT) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= max_length


def _valid_refs(refs: object) -> bool:
    return (
        isinstance(refs, tuple)
        and bool(refs)
        and len(set(refs)) == len(refs)
        and all(_valid_text(ref, _MAX_REF) for ref in refs)
    )


def validate_commercial_mandate(mandate: CommercialMandate) -> tuple[str, ...]:
    if not isinstance(mandate, CommercialMandate):
        return ("mandate must be a CommercialMandate",)

    errors: list[str] = []
    for name, value in (
        ("mandate_id", mandate.mandate_id),
        ("project_ref", mandate.project_ref),
        ("campaign_ref", mandate.campaign_ref),
    ):
        if not _valid_text(value, _MAX_REF):
            errors.append(f"{name} is invalid")

    if not _valid_refs(mandate.source_version_refs):
        errors.append("source_version_refs are invalid")
    if not _valid_refs(mandate.allowed_product_refs):
        errors.append("allowed_product_refs are invalid")

    if (
        not isinstance(mandate.allowed_channels, tuple)
        or not mandate.allowed_channels
        or len(set(mandate.allowed_channels)) != len(mandate.allowed_channels)
        or any(channel not in _ALLOWED_CHANNELS for channel in mandate.allowed_channels)
    ):
        errors.append("allowed_channels are invalid")

    created = _parse_time(mandate.created_at)
    expires = _parse_time(mandate.expires_at)
    if created is None:
        errors.append("created_at must be timezone-aware ISO-8601")
    if expires is None:
        errors.append("expires_at must be timezone-aware ISO-8601")
    if created is not None and expires is not None:
        lifetime_hours = (expires - created).total_seconds() / 3600
        if lifetime_hours <= 0:
            errors.append("expires_at must be later than created_at")
        elif lifetime_hours > _MAX_MANDATE_HOURS:
            errors.append("mandate lifetime exceeds maximum")

    if not isinstance(mandate.max_targets, int) or isinstance(mandate.max_targets, bool):
        errors.append("max_targets must be an integer")
    elif not 1 <= mandate.max_targets <= _MAX_TARGETS:
        errors.append("max_targets is outside allowed bounds")

    if not isinstance(mandate.max_messages_per_target, int) or isinstance(mandate.max_messages_per_target, bool):
        errors.append("max_messages_per_target must be an integer")
    elif not 1 <= mandate.max_messages_per_target <= _MAX_MESSAGES_PER_TARGET:
        errors.append("max_messages_per_target is outside allowed bounds")

    if not isinstance(mandate.allow_nonbinding_negotiation, bool):
        errors.append("allow_nonbinding_negotiation must be a boolean")

    return tuple(errors)


def commercial_mandate_digest(mandate: CommercialMandate) -> str:
    payload = {
        "mandate_id": mandate.mandate_id,
        "project_ref": mandate.project_ref,
        "campaign_ref": mandate.campaign_ref,
        "created_at": mandate.created_at,
        "expires_at": mandate.expires_at,
        "source_version_refs": list(mandate.source_version_refs),
        "allowed_channels": list(mandate.allowed_channels),
        "allowed_product_refs": list(mandate.allowed_product_refs),
        "max_targets": mandate.max_targets,
        "max_messages_per_target": mandate.max_messages_per_target,
        "allow_nonbinding_negotiation": mandate.allow_nonbinding_negotiation,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def mandate_action_id(mandate: CommercialMandate) -> str:
    return f"commercial-mandate:{mandate.mandate_id}:{commercial_mandate_digest(mandate)}"


def validate_mandate_approval(mandate: CommercialMandate, approval: ActionApproval) -> MandateDecision:
    errors = validate_commercial_mandate(mandate)
    if errors:
        return MandateDecision(False, False, "; ".join(errors))
    if not isinstance(approval, ActionApproval):
        return MandateDecision(False, False, "approval must be an ActionApproval")
    if approval.approved is not True:
        return MandateDecision(False, False, "commercial mandate is not approved")
    if approval.action_id != mandate_action_id(mandate):
        return MandateDecision(False, False, "approval does not match exact mandate digest")
    return MandateDecision(True, False, "exact bounded commercial mandate approved")


def evaluate_commercial_action(
    mandate: CommercialMandate,
    approval: ActionApproval,
    action: CommercialAction,
    *,
    now: datetime | None = None,
) -> MandateDecision:
    """Authorize routine work inside an approved mandate while blocking binding acts.

    This is the core 'autopilot until Deal/No-Deal' rule. External messages may proceed
    without per-message approval only when the exact mandate was approved and the action
    remains within project, campaign, channel, message-count and non-binding boundaries.
    """

    mandate_gate = validate_mandate_approval(mandate, approval)
    if not mandate_gate.allowed_now:
        return mandate_gate
    if not isinstance(action, CommercialAction):
        return MandateDecision(False, False, "action must be a CommercialAction")

    expires = _parse_time(mandate.expires_at)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    assert expires is not None
    if current >= expires:
        return MandateDecision(False, False, "commercial mandate expired")

    if not _valid_text(action.action_id, _MAX_REF):
        return MandateDecision(False, False, "action_id is invalid")
    if not _valid_text(action.target_ref, _MAX_REF):
        return MandateDecision(False, False, "target_ref is invalid")
    if action.project_ref != mandate.project_ref:
        return MandateDecision(False, False, "project_ref is outside mandate")
    if action.campaign_ref != mandate.campaign_ref:
        return MandateDecision(False, False, "campaign_ref is outside mandate")

    if action.kind in _BINDING_ACTIONS:
        return MandateDecision(False, True, f"{action.kind} requires final Deal/No-Deal gate")
    if action.kind not in _ROUTINE_AUTONOMOUS_ACTIONS:
        return MandateDecision(False, False, "unsupported commercial action")

    if action.kind in {"send_intro", "send_followup", "ask_clarification", "request_meeting", "request_quote", "nonbinding_negotiate"}:
        if action.channel not in mandate.allowed_channels:
            return MandateDecision(False, False, "channel is outside mandate")
        if action.message_ordinal < 1 or action.message_ordinal > mandate.max_messages_per_target:
            return MandateDecision(False, False, "message ordinal exceeds mandate")
        if not _valid_text(action.content_digest, _MAX_REF):
            return MandateDecision(False, False, "message action requires content_digest")

    if action.kind == "nonbinding_negotiate" and not mandate.allow_nonbinding_negotiation:
        return MandateDecision(False, False, "non-binding negotiation is disabled by mandate")

    return MandateDecision(True, False, "routine commercial action allowed by exact mandate")


def validate_deal_packet(packet: DealDecisionPacket) -> tuple[str, ...]:
    if not isinstance(packet, DealDecisionPacket):
        return ("packet must be a DealDecisionPacket",)
    errors: list[str] = []
    for name, value in (
        ("packet_id", packet.packet_id),
        ("project_ref", packet.project_ref),
        ("counterparty_ref", packet.counterparty_ref),
    ):
        if not _valid_text(value, _MAX_REF):
            errors.append(f"{name} is invalid")

    for name, refs in (
        ("source_version_refs", packet.source_version_refs),
        ("technical_fit_refs", packet.technical_fit_refs),
        ("commercial_terms_refs", packet.commercial_terms_refs),
        ("compliance_refs", packet.compliance_refs),
        ("risk_refs", packet.risk_refs),
    ):
        if not _valid_refs(refs):
            errors.append(f"{name} are invalid")

    if not isinstance(packet.open_issue_refs, tuple) or len(set(packet.open_issue_refs)) != len(packet.open_issue_refs):
        errors.append("open_issue_refs are invalid")
    elif any(not _valid_text(ref, _MAX_REF) for ref in packet.open_issue_refs):
        errors.append("open_issue_refs are invalid")

    if packet.recommendation not in {"deal", "no_deal", "conditional", "insufficient_evidence"}:
        errors.append("recommendation is invalid")
    return tuple(errors)


def final_deal_action_id(packet: DealDecisionPacket, decision: Literal["deal", "no_deal"]) -> str:
    payload = {
        "packet_id": packet.packet_id,
        "project_ref": packet.project_ref,
        "counterparty_ref": packet.counterparty_ref,
        "source_version_refs": list(packet.source_version_refs),
        "technical_fit_refs": list(packet.technical_fit_refs),
        "commercial_terms_refs": list(packet.commercial_terms_refs),
        "compliance_refs": list(packet.compliance_refs),
        "risk_refs": list(packet.risk_refs),
        "open_issue_refs": list(packet.open_issue_refs),
        "recommendation": packet.recommendation,
        "decision": decision,
    }
    digest = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"final-deal:{packet.packet_id}:{decision}:{digest}"


def authorize_final_deal(
    packet: DealDecisionPacket,
    decision: Literal["deal", "no_deal"],
    *,
    approval: ActionApproval,
) -> FinalDealDecision:
    errors = validate_deal_packet(packet)
    action_id = final_deal_action_id(packet, decision)
    if errors:
        return FinalDealDecision(packet.packet_id, decision, GateDecision(False, False, "; ".join(errors)))
    if not isinstance(approval, ActionApproval):
        return FinalDealDecision(packet.packet_id, decision, GateDecision(False, True, "final deal approval is required"))
    if approval.approved is not True or approval.action_id != action_id:
        return FinalDealDecision(packet.packet_id, decision, GateDecision(False, True, "approval does not match exact final deal packet"))
    return FinalDealDecision(packet.packet_id, decision, GateDecision(True, False, "exact final Deal/No-Deal decision approved"))


def ready_for_final_decision(packet: DealDecisionPacket) -> bool:
    """Return True only when the packet is evidence-complete and has no open issues."""

    return not validate_deal_packet(packet) and not packet.open_issue_refs and packet.recommendation in {"deal", "no_deal"}


def choose_next_commercial_action(actions: Sequence[CommercialAction]) -> CommercialAction | None:
    """Deterministically pick the next non-binding action from a prepared queue.

    The queue is intentionally not a business-score engine. It only gives priority to
    evidence/qualification work before outbound, then clarification/quote collection,
    then non-binding negotiation and final-packet preparation.
    """

    rank = {
        "discover": 0,
        "qualify": 1,
        "draft": 2,
        "send_intro": 3,
        "ask_clarification": 4,
        "request_quote": 5,
        "request_meeting": 6,
        "send_followup": 7,
        "nonbinding_negotiate": 8,
        "prepare_deal_packet": 9,
    }
    candidates = [action for action in actions if isinstance(action, CommercialAction) and action.kind in rank]
    if not candidates:
        return None
    return sorted(candidates, key=lambda action: (rank[action.kind], action.action_id))[0]
