from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class OutcomeDecision(str, Enum):
    INSUFFICIENT = "insufficient"
    REGRESSED = "regressed"
    UNCHANGED = "unchanged"
    IMPROVED = "improved"


@dataclass(frozen=True)
class OutcomeSignal:
    signal_id: str
    decision_id: str
    metric_name: str
    baseline: float
    candidate: float
    evidence_refs: tuple[str, ...]
    higher_is_better: bool = True
    terminal_outcome_observed: bool = False

    def __post_init__(self) -> None:
        for name, value in (("signal_id", self.signal_id), ("decision_id", self.decision_id), ("metric_name", self.metric_name)):
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be a normalized non-empty string")
        for name, value in (("baseline", self.baseline), ("candidate", self.candidate)):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite numeric")
        if not isinstance(self.higher_is_better, bool) or not isinstance(self.terminal_outcome_observed, bool):
            raise ValueError("outcome flags must be boolean")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise ValueError("evidence_refs are required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("evidence_refs must be unique")
        for ref in self.evidence_refs:
            if not isinstance(ref, str) or not ref.strip() or ref != ref.strip():
                raise ValueError("evidence_refs must be normalized non-empty strings")

    @property
    def normalized_gain(self) -> float:
        raw = float(self.candidate) - float(self.baseline)
        return raw if self.higher_is_better else -raw


@dataclass(frozen=True)
class OutcomeGateResult:
    decision: OutcomeDecision
    signal_refs: tuple[str, ...]
    terminal_evidence_present: bool
    promotion_support: bool


def evaluate_outcomes(
    signals: tuple[OutcomeSignal, ...],
    *,
    require_terminal_outcome: bool = False,
    minimum_gain: float = 0.0,
) -> OutcomeGateResult:
    """Evaluate observed outcomes without replacing PR #7 decision-learning authority.

    This gate consumes externally recorded decision/outcome evidence. It does not infer
    missing business outcomes and never authorizes execution or promotion by itself.
    """
    if not isinstance(signals, tuple):
        raise ValueError("signals must be a tuple")
    if not isinstance(require_terminal_outcome, bool):
        raise ValueError("require_terminal_outcome must be boolean")
    if not isinstance(minimum_gain, (int, float)) or isinstance(minimum_gain, bool) or not math.isfinite(float(minimum_gain)) or minimum_gain < 0:
        raise ValueError("minimum_gain must be finite and non-negative")
    if not signals:
        return OutcomeGateResult(OutcomeDecision.INSUFFICIENT, (), False, False)

    ids: set[str] = set()
    terminal = False
    gains: list[float] = []
    for signal in signals:
        if not isinstance(signal, OutcomeSignal):
            raise ValueError("signals must contain OutcomeSignal")
        if signal.signal_id in ids:
            raise ValueError("duplicate signal_id")
        ids.add(signal.signal_id)
        terminal = terminal or signal.terminal_outcome_observed
        gains.append(signal.normalized_gain)

    refs = tuple(signal.signal_id for signal in signals)
    if require_terminal_outcome and not terminal:
        return OutcomeGateResult(OutcomeDecision.INSUFFICIENT, refs, False, False)
    if any(gain < 0 for gain in gains):
        return OutcomeGateResult(OutcomeDecision.REGRESSED, refs, terminal, False)
    if any(gain < float(minimum_gain) for gain in gains):
        return OutcomeGateResult(OutcomeDecision.UNCHANGED, refs, terminal, False)
    if all(gain == 0 for gain in gains) and minimum_gain == 0:
        return OutcomeGateResult(OutcomeDecision.UNCHANGED, refs, terminal, False)
    return OutcomeGateResult(OutcomeDecision.IMPROVED, refs, terminal, True)
