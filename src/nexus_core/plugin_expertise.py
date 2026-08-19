from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

Maturity = Literal["unknown", "discovered", "authenticated", "read_verified", "write_verified"]
Risk = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class PluginExpertise:
    name: str
    domain: str
    best_for: tuple[str, ...]
    maturity: Maturity
    risk: Risk = "low"
    parallel_safe: bool = True
    evidence_ref: str | None = None


@dataclass(frozen=True)
class WorkLane:
    name: str
    required_domain: str
    value: int
    urgency: int
    external_effect: bool = False


@dataclass(frozen=True)
class LaneAssignment:
    lane: str
    plugin: str | None
    human_gate: bool
    reason: str


def _validate_score(value: int) -> None:
    if not 0 <= value <= 100:
        raise ValueError("score_out_of_range")


def assign_parallel_lanes(
    plugins: Iterable[PluginExpertise],
    lanes: Iterable[WorkLane],
    *,
    max_parallel: int = 4,
) -> tuple[LaneAssignment, ...]:
    if max_parallel < 1:
        raise ValueError("invalid_parallelism")
    pool = tuple(plugins)
    work = tuple(lanes)
    if len({p.name for p in pool}) != len(pool):
        raise ValueError("duplicate_plugin")
    if len({w.name for w in work}) != len(work):
        raise ValueError("duplicate_lane")
    for lane in work:
        _validate_score(lane.value)
        _validate_score(lane.urgency)

    ranked = sorted(work, key=lambda w: (-w.value, -w.urgency, w.name))[:max_parallel]
    out: list[LaneAssignment] = []
    for lane in ranked:
        candidates = [
            p for p in pool
            if p.domain == lane.required_domain
            and p.maturity in {"read_verified", "write_verified"}
            and p.parallel_safe
        ]
        candidates.sort(key=lambda p: (
            0 if p.maturity == "write_verified" else 1,
            0 if p.risk == "low" else 1 if p.risk == "medium" else 2,
            p.name,
        ))
        if not candidates:
            out.append(LaneAssignment(lane.name, None, lane.external_effect, "no_verified_specialist"))
            continue
        chosen = candidates[0]
        out.append(LaneAssignment(
            lane.name,
            chosen.name,
            lane.external_effect or chosen.risk == "high",
            "verified_specialist",
        ))
    return tuple(out)
