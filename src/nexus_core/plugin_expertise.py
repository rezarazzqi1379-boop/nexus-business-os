from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

Maturity = Literal["unknown", "discovered", "authenticated", "read_verified", "write_verified"]
Risk = Literal["low", "medium", "high"]

_ALLOWED_MATURITY = {"unknown", "discovered", "authenticated", "read_verified", "write_verified"}
_ALLOWED_RISK = {"low", "medium", "high"}
_VERIFIED_MATURITY = {"read_verified", "write_verified"}
_MAX_TEXT = 256


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


def _valid_compact_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= _MAX_TEXT


def _validate_score(value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
        raise ValueError("score_out_of_range")


def _validate_plugin(plugin: object) -> None:
    if not isinstance(plugin, PluginExpertise):
        raise ValueError("invalid_plugin")
    if not _valid_compact_text(plugin.name):
        raise ValueError("invalid_plugin_name")
    if not _valid_compact_text(plugin.domain):
        raise ValueError("invalid_plugin_domain")
    if not isinstance(plugin.best_for, tuple) or not plugin.best_for or any(
        not _valid_compact_text(item) for item in plugin.best_for
    ):
        raise ValueError("invalid_plugin_best_for")
    if plugin.maturity not in _ALLOWED_MATURITY:
        raise ValueError("invalid_plugin_maturity")
    if plugin.risk not in _ALLOWED_RISK:
        raise ValueError("invalid_plugin_risk")
    if not isinstance(plugin.parallel_safe, bool):
        raise ValueError("invalid_parallel_safe")
    if plugin.maturity in _VERIFIED_MATURITY:
        if not _valid_compact_text(plugin.evidence_ref):
            raise ValueError("verified_plugin_requires_evidence_ref")
    elif plugin.evidence_ref is not None and not _valid_compact_text(plugin.evidence_ref):
        raise ValueError("invalid_plugin_evidence_ref")


def _validate_lane(lane: object) -> None:
    if not isinstance(lane, WorkLane):
        raise ValueError("invalid_lane")
    if not _valid_compact_text(lane.name):
        raise ValueError("invalid_lane_name")
    if not _valid_compact_text(lane.required_domain):
        raise ValueError("invalid_required_domain")
    _validate_score(lane.value)
    _validate_score(lane.urgency)
    if not isinstance(lane.external_effect, bool):
        raise ValueError("invalid_external_effect")


def assign_parallel_lanes(
    plugins: Iterable[PluginExpertise],
    lanes: Iterable[WorkLane],
    *,
    max_parallel: int = 4,
) -> tuple[LaneAssignment, ...]:
    if not isinstance(max_parallel, int) or isinstance(max_parallel, bool) or max_parallel < 1:
        raise ValueError("invalid_parallelism")
    try:
        pool = tuple(plugins)
        work = tuple(lanes)
    except TypeError as exc:
        raise ValueError("plugins_and_lanes_must_be_iterable") from exc

    for plugin in pool:
        _validate_plugin(plugin)
    for lane in work:
        _validate_lane(lane)

    if len({p.name for p in pool}) != len(pool):
        raise ValueError("duplicate_plugin")
    if len({w.name for w in work}) != len(work):
        raise ValueError("duplicate_lane")

    ranked = sorted(work, key=lambda w: (-w.value, -w.urgency, w.name))[:max_parallel]
    out: list[LaneAssignment] = []
    for lane in ranked:
        candidates = [
            p for p in pool
            if p.domain == lane.required_domain
            and p.maturity in _VERIFIED_MATURITY
            and p.parallel_safe
            and _valid_compact_text(p.evidence_ref)
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
