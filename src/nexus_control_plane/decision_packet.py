from __future__ import annotations

from dataclasses import dataclass


_ALLOWED_APPROVAL_CLASSES = {"internal_read", "internal_write", "external_reversible", "external_consequential"}


def _valid_ref_tuple(values: object, *, required: bool = False) -> bool:
    if not isinstance(values, tuple):
        return False
    if required and not values:
        return False
    if any(not isinstance(v, str) or not v.strip() or v != v.strip() for v in values):
        return False
    return len(values) == len(set(values))


@dataclass(frozen=True)
class DecisionPacket:
    packet_id: str
    project_id: str
    subject: str
    canonical_source_refs: tuple[str, ...]
    live_evidence_refs: tuple[str, ...]
    claim_refs: tuple[str, ...]
    unknowns: tuple[str, ...]
    contradiction_refs: tuple[str, ...]
    failure_refs: tuple[str, ...]
    decision_ref: str
    outcome_target: str
    approval_class: str
    action_ref: str | None = None
    outcome_refs: tuple[str, ...] = ()


def validate_decision_packet(packet: DecisionPacket, *, consequential: bool) -> tuple[str, ...]:
    """Validate the minimum context needed for a material NEXUS decision.

    The packet is an adapter: it references canonical sources, evidence, decisions,
    contradictions, failures and outcomes but does not become authority for any of them.
    """
    if not isinstance(packet, DecisionPacket):
        return ("packet must be DecisionPacket",)
    if not isinstance(consequential, bool):
        return ("consequential must be boolean",)

    errors: list[str] = []
    for name in ("packet_id", "project_id", "subject", "decision_ref", "outcome_target", "approval_class"):
        value = getattr(packet, name)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            errors.append(f"{name} is invalid")

    for name, required in (
        ("canonical_source_refs", True),
        ("live_evidence_refs", False),
        ("claim_refs", False),
        ("unknowns", False),
        ("contradiction_refs", False),
        ("failure_refs", False),
        ("outcome_refs", False),
    ):
        if not _valid_ref_tuple(getattr(packet, name), required=required):
            errors.append(f"{name} must be unique normalized strings" + (" and non-empty" if required else ""))

    if packet.approval_class not in _ALLOWED_APPROVAL_CLASSES:
        errors.append("approval_class is unsupported")
    if consequential and packet.approval_class != "external_consequential":
        errors.append("consequential external decision requires external_consequential approval class")
    if packet.action_ref is not None and (not isinstance(packet.action_ref, str) or not packet.action_ref.strip() or packet.action_ref != packet.action_ref.strip()):
        errors.append("action_ref must be None or a normalized string")
    if packet.contradiction_refs:
        errors.append("open contradiction references must be resolved before consequential decision release")
    if consequential and not packet.live_evidence_refs:
        errors.append("consequential decision requires current live evidence references")
    if consequential and packet.unknowns:
        errors.append("consequential decision with unresolved material unknowns requires hold/review")
    return tuple(errors)
