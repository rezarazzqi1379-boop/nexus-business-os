from datetime import datetime, timedelta, timezone

import pytest

from nexus_core.asset_memory import AssetRecord
from nexus_core.asset_reanalysis import plan_reanalysis


def asset(state: str, observed: datetime) -> AssetRecord:
    return AssetRecord(
        asset_id=f"a-{state}", file_name="x.pdf", source="file_library", kind="pdf",
        stable_ref="file://x", source_version_ref="v1", observed_at=observed,
        project_refs=("p",), goal_refs=("g",), evidence_refs=("e",), analysis_state=state,
    )


def test_stale_is_immediate_high_priority():
    now = datetime(2026, 8, 20, tzinfo=timezone.utc)
    result = plan_reanalysis(asset("stale", now), now=now)
    assert result.should_reanalyze is True
    assert result.priority == 100


def test_old_analyzed_asset_requeues():
    now = datetime(2026, 8, 20, tzinfo=timezone.utc)
    result = plan_reanalysis(asset("analyzed", now - timedelta(days=31)), now=now)
    assert result.should_reanalyze is True
    assert result.reason == "age_threshold"


def test_future_observed_at_fails_closed():
    now = datetime(2026, 8, 20, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="future_observed_at"):
        plan_reanalysis(asset("analyzed", now + timedelta(seconds=1)), now=now)
