from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryAction(str, Enum):
    CONTINUE = "continue"
    RETRY_LOCAL = "retry_local"
    REPLAN_FROM_CHECKPOINT = "replan_from_checkpoint"
    REWIND = "rewind"
    HUMAN_HOLD = "human_hold"


@dataclass(frozen=True)
class RecoveryCheckpoint:
    checkpoint_id: str
    state_ref: str
    evidence_refs: tuple[str, ...]
    verified: bool
    reversible: bool
    consequence_level: int = 0


@dataclass(frozen=True)
class RecoveryInput:
    failure_class: str
    local_failure: bool
    state_corrupted: bool
    repeated_attempts: int
    max_retries: int
    consequential: bool
    checkpoints: tuple[RecoveryCheckpoint, ...]


@dataclass(frozen=True)
class RecoveryDecision:
    action: RecoveryAction
    checkpoint_id: str | None
    reasons: tuple[str, ...]


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _usable_checkpoint(cp: RecoveryCheckpoint) -> bool:
    return (
        isinstance(cp, RecoveryCheckpoint)
        and _clean(cp.checkpoint_id)
        and _clean(cp.state_ref)
        and isinstance(cp.evidence_refs, tuple)
        and bool(cp.evidence_refs)
        and all(_clean(x) for x in cp.evidence_refs)
        and cp.verified
        and cp.reversible
        and isinstance(cp.consequence_level, int)
        and 0 <= cp.consequence_level <= 3
    )


def decide_recovery(inp: RecoveryInput) -> RecoveryDecision:
    """Choose bounded recovery from verified state, never blind infinite retry.

    The newest usable checkpoint is assumed to be the last tuple item. Consequential
    failures never auto-rewind; they hold for human review even when a reversible
    checkpoint exists.
    """
    if not isinstance(inp, RecoveryInput):
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid recovery input",))
    if not _clean(inp.failure_class):
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid failure class",))
    if not isinstance(inp.repeated_attempts, int) or inp.repeated_attempts < 0:
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid repeated_attempts",))
    if not isinstance(inp.max_retries, int) or inp.max_retries < 0:
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid max_retries",))
    if not all(isinstance(v, bool) for v in (inp.local_failure, inp.state_corrupted, inp.consequential)):
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid boolean recovery flags",))
    if not isinstance(inp.checkpoints, tuple):
        return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("invalid checkpoints",))

    usable = tuple(cp for cp in inp.checkpoints if _usable_checkpoint(cp))
    latest = usable[-1] if usable else None

    if inp.consequential:
        return RecoveryDecision(
            RecoveryAction.HUMAN_HOLD,
            latest.checkpoint_id if latest else None,
            ("consequential failure requires reviewed recovery",),
        )

    if inp.state_corrupted:
        if latest is None:
            return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("no verified reversible checkpoint available",))
        return RecoveryDecision(
            RecoveryAction.REWIND,
            latest.checkpoint_id,
            ("state corruption detected", "rewind to latest verified reversible checkpoint"),
        )

    if inp.local_failure and inp.repeated_attempts < inp.max_retries:
        return RecoveryDecision(
            RecoveryAction.RETRY_LOCAL,
            latest.checkpoint_id if latest else None,
            ("failure is isolated", "bounded local retry remains available"),
        )

    if latest is not None:
        return RecoveryDecision(
            RecoveryAction.REPLAN_FROM_CHECKPOINT,
            latest.checkpoint_id,
            ("retry budget exhausted or failure is non-local", "replan from verified state rather than full restart"),
        )

    return RecoveryDecision(RecoveryAction.HUMAN_HOLD, None, ("no safe recovery path established",))
