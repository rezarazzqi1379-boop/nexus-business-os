from dataclasses import dataclass
from typing import Iterable, Literal

from nexus_core.autonomy import WorkItem

SignalKind = Literal[
    "supplier_reply",
    "customer_signal",
    "technical_mismatch",
    "market_opportunity",
    "project_risk",
]

_PRIORITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_EVIDENCE = {"strong": 0, "partial": 1, "weak": 2, "unverified": 3}
_COST = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class ProjectSignal:
    signal_id: str
    project_id: str
    kind: SignalKind
    summary: str
    evidence_refs: tuple[str, ...]
    value: str = "medium"
    urgency: str = "medium"
    evidence: str = "partial"
    cost: str = "low"


@dataclass(frozen=True)
class RoutedSignal:
    signal: ProjectSignal
    work_item: WorkItem


def _validate(signal: ProjectSignal) -> None:
    for name, value in (("signal_id", signal.signal_id), ("project_id", signal.project_id), ("summary", signal.summary)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonblank string")
    if not signal.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in signal.evidence_refs):
        raise ValueError("evidence_refs must contain at least one retrievable reference")
    if signal.value not in _PRIORITY or signal.urgency not in _PRIORITY:
        raise ValueError("unsupported priority tier")
    if signal.evidence not in _EVIDENCE:
        raise ValueError("unsupported evidence tier")
    if signal.cost not in _COST:
        raise ValueError("unsupported cost tier")


def signal_to_work_item(signal: ProjectSignal) -> WorkItem:
    """Convert a live signal into research-only governed work.

    Routing never grants outreach or other consequential authority. Every generated
    task re-enters the existing capability planner and policy gate.
    """
    _validate(signal)
    objective = f"Investigate {signal.project_id}: {signal.summary}"
    return WorkItem(
        task_id=f"signal:{signal.signal_id}",
        domain="research",
        objective=objective,
        action_kind="research",
        acceptable_capability_ids=("web_research", "connected_source_read"),
        evidence_refs=signal.evidence_refs,
        value=signal.value,
        urgency=signal.urgency,
        evidence=signal.evidence,
        cost=signal.cost,
        write_required=False,
        reversible=True,
        goal_ref=f"project:{signal.project_id}",
        success_signal="verified decision-relevant finding with retrievable evidence",
        failure_signal="insufficient evidence or unresolved contradiction",
    )


def route_signals(signals: Iterable[ProjectSignal]) -> tuple[RoutedSignal, ...]:
    seen: set[str] = set()
    routed: list[RoutedSignal] = []
    for signal in signals:
        _validate(signal)
        if signal.signal_id in seen:
            continue
        seen.add(signal.signal_id)
        routed.append(RoutedSignal(signal=signal, work_item=signal_to_work_item(signal)))

    routed.sort(
        key=lambda item: (
            _PRIORITY[item.signal.value],
            _PRIORITY[item.signal.urgency],
            _EVIDENCE[item.signal.evidence],
            _COST[item.signal.cost],
            item.signal.project_id,
            item.signal.signal_id,
        )
    )
    return tuple(routed)
