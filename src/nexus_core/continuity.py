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
    """Build a recovery-first bootstrap instruction for a new NEXUS session.

    The packet is continuity input, never authority. Mutable live systems must win over
    remembered or static state. Conflict is surfaced explicitly rather than silently
    reconciled, because a convenient merge can turn stale context into false truth.
    """
    errors = validate_continuity_packet(packet)
    if errors:
        raise ValueError("invalid continuity packet: " + "; ".join(errors))
    return (
        "Resume NEXUS from this packet as canonical continuity input, not authorization. "
        "Recover the operating contract, Goal Portfolio, active work, blockers, evidence, experiments and Human Gates. "
        "Then live-verify every mutable dependency that can change the next decision, prioritizing GitHub/CI, Gmail, Notion, Supabase, Vercel, Drive and Capability Health when referenced or available. "
        "If live evidence conflicts with this packet or remembered chat context, preserve both refs, mark the old state stale, and let current verified evidence win; never silently merge contradictory state. "
        "Do not create a replacement registry, checkpoint, database, agent or source merely to reconcile drift. "
        "Classify each active goal as next_action, waiting_blocked, scheduled_review or explicit_pause; require measurable success/failure signals for meaningful work. "
        "Continue the highest-value reversible internal work automatically, favoring current commercial blockers, qualified network paths, tested code/security hardening and restore-readiness over architecture accumulation. "
        "Before any consequential action, preserve explicit human approval for external send, protected/main merge, production deploy, permission/access change, publication, payment, contract/signature, destructive action or material Supabase write. "
        "At the end of the recovery pass, record only net-new verified state: current refs, changed blockers, measurable outcomes, failed assumptions and the next smallest high-value action. "
        + packet.next_resume_instruction
    )
