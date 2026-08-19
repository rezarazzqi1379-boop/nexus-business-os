from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .asset_memory import AssetRecord, validate_asset


@dataclass(frozen=True)
class ReanalysisDecision:
    asset_id: str
    should_reanalyze: bool
    reason: str
    priority: int


def plan_reanalysis(asset: AssetRecord, *, now: datetime, max_age: timedelta = timedelta(days=30)) -> ReanalysisDecision:
    errors = validate_asset(asset)
    if errors:
        raise ValueError(",".join(errors))
    if now.tzinfo is None:
        raise ValueError("timezone_naive_now")
    if asset.analysis_state in {"unseen", "stale"}:
        return ReanalysisDecision(asset.asset_id, True, asset.analysis_state, 100)
    if asset.analysis_state == "blocked":
        return ReanalysisDecision(asset.asset_id, False, "blocked", 0)
    age = now - asset.observed_at
    if age < timedelta(0):
        raise ValueError("future_observed_at")
    if age > max_age and (asset.project_refs or asset.goal_refs):
        return ReanalysisDecision(asset.asset_id, True, "age_threshold", 70)
    return ReanalysisDecision(asset.asset_id, False, "fresh", 10)
