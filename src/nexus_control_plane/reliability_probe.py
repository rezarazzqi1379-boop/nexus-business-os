from __future__ import annotations

from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
class ReliabilityRun:
    run_id: str
    success: bool
    latency_ms: int
    tool_calls: int
    context_units: int
    semantic_check_passed: bool


@dataclass(frozen=True)
class ReliabilitySnapshot:
    run_count: int
    success_rate: float
    semantic_success_rate: float
    all_runs_success: bool
    p50_latency_ms: int
    p95_latency_ms: int
    min_tool_calls: int
    max_tool_calls: int
    min_context_units: int
    max_context_units: int


def _valid_run(run: ReliabilityRun) -> bool:
    if not isinstance(run, ReliabilityRun):
        return False
    if not isinstance(run.run_id, str) or not run.run_id.strip() or run.run_id != run.run_id.strip():
        return False
    if not isinstance(run.success, bool) or not isinstance(run.semantic_check_passed, bool):
        return False
    for field in ("latency_ms", "tool_calls", "context_units"):
        value = getattr(run, field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return False
    return True


def _percentile95(values: tuple[int, ...]) -> int:
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ((95 * len(ordered) + 99) // 100) - 1))
    return ordered[index]


def summarize_reliability(runs: tuple[ReliabilityRun, ...]) -> ReliabilitySnapshot:
    """Measure repeated-run reliability and semantic correctness separately.

    A structurally successful run is not counted as semantically correct unless
    the independent semantic check also passes. This prevents clean telemetry
    from being mistaken for correct behavior.
    """
    if not isinstance(runs, tuple) or not runs:
        raise ValueError("runs must be a non-empty tuple")
    if any(not _valid_run(run) for run in runs):
        raise ValueError("invalid reliability run")
    ids = tuple(run.run_id for run in runs)
    if len(set(ids)) != len(ids):
        raise ValueError("run ids must be unique")

    latencies = tuple(run.latency_ms for run in runs)
    tools = tuple(run.tool_calls for run in runs)
    contexts = tuple(run.context_units for run in runs)
    successes = sum(run.success for run in runs)
    semantic_successes = sum(run.success and run.semantic_check_passed for run in runs)
    return ReliabilitySnapshot(
        run_count=len(runs),
        success_rate=successes / len(runs),
        semantic_success_rate=semantic_successes / len(runs),
        all_runs_success=successes == len(runs) and semantic_successes == len(runs),
        p50_latency_ms=int(median(latencies)),
        p95_latency_ms=_percentile95(latencies),
        min_tool_calls=min(tools),
        max_tool_calls=max(tools),
        min_context_units=min(contexts),
        max_context_units=max(contexts),
    )
