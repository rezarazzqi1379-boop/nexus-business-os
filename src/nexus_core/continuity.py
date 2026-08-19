from dataclasses import dataclass
from datetime import datetime
from typing import Sequence
from unicodedata import category

_DISALLOWED = {"Cc", "Cf", "Zl", "Zp"}
_MAX_META = 256
_MAX_TEXT = 4096


@dataclass(frozen=True)
class ContinuityPacket:
    packet_id: str
    created_at: str
    source_version_ref: str
    operating_contract_ref: str
    goal_portfolio_ref: str
    active_work_refs: tuple[str, ...]
    blocker_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    human_gate_refs: tuple[str, ...]
    next_resume_instruction: str


def _text_error(name: str, value: object, max_len: int) -> str | None:
    if not isinstance(value, str): return f"{name} must be a string"
    if not value.strip(): return f"{name} is required"
    if value != value.strip(): return f"{name} cannot have leading or trailing whitespace"
    if len(value) > max_len: return f"{name} must be at most {max_len} characters"
    if any(category(ch) in _DISALLOWED for ch in value): return f"{name} cannot contain control or formatting characters"
    return None


def _refs_error(name: str, refs: object) -> list[str]:
    if not isinstance(refs, tuple): return [f"{name} must be a tuple"]
    errors: list[str] = []; seen: set[str] = set()
    for ref in refs:
        error = _text_error(name, ref, _MAX_META)
        if error: errors.append(error)
        if isinstance(ref, str):
            if ref in seen: errors.append(f"{name} cannot contain duplicates")
            seen.add(ref)
    return errors


def validate_continuity_packet(packet: ContinuityPacket) -> list[str]:
    if not isinstance(packet, ContinuityPacket): return ["packet must be a ContinuityPacket"]
    errors: list[str] = []
    for name, value in (
        ("packet_id", packet.packet_id),
        ("source_version_ref", packet.source_version_ref),
        ("operating_contract_ref", packet.operating_contract_ref),
        ("goal_portfolio_ref", packet.goal_portfolio_ref),
    ):
        error = _text_error(name, value, _MAX_META)
        if error: errors.append(error)
    error = _text_error("next_resume_instruction", packet.next_resume_instruction, _MAX_TEXT)
    if error: errors.append(error)
    try:
        created = datetime.fromisoformat(packet.created_at.replace("Z", "+00:00"))
        if created.tzinfo is None: errors.append("created_at must include a timezone offset")
    except (AttributeError, ValueError):
        errors.append("created_at must be ISO-8601")
    for name, refs in (
        ("active_work_refs", packet.active_work_refs),
        ("blocker_refs", packet.blocker_refs),
        ("evidence_refs", packet.evidence_refs),
        ("human_gate_refs", packet.human_gate_refs),
    ):
        errors.extend(_refs_error(name, refs))
    if not packet.evidence_refs:
        errors.append("evidence_refs requires at least one retrievable reference")
    return errors


def build_resume_instruction(packet: ContinuityPacket) -> str:
    errors = validate_continuity_packet(packet)
    if errors:
        raise ValueError("invalid continuity packet: " + "; ".join(errors))
    return (
        "Resume NEXUS from this packet as canonical continuity input. Verify source/version refs before acting; "
        "recover the current Goal Portfolio, active work, blockers, evidence and human gates; do not invent missing state; "
        "continue only reversible internal work automatically; preserve human approval for consequential external actions. "
        + packet.next_resume_instruction
    )
