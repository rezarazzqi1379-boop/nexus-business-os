from datetime import datetime, timezone

from nexus_core.asset_analysis import AnalysisResult, queue_asset_analysis, validate_analysis_result
from nexus_core.asset_memory import AssetRecord


def asset(**overrides):
    base = dict(
        asset_id="img-1",
        file_name="machine.png",
        source="chat_attachment",
        kind="image",
        stable_ref="chat:file-1",
        source_version_ref="v1",
        observed_at=datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc),
        project_refs=("hydrotester",),
        goal_refs=("commercial",),
        evidence_refs=("chat:file-1",),
        sensitivity="internal",
        analysis_state="unseen",
    )
    base.update(overrides)
    return AssetRecord(**base)


def test_image_routes_to_vision_and_active_project_is_prioritized():
    tasks = queue_asset_analysis((asset(),), active_project_refs=("hydrotester",))
    assert tasks[0].route == "vision_analysis"
    assert tasks[0].priority >= 100


def test_analyzed_asset_is_not_requeued():
    assert queue_asset_analysis((asset(analysis_state="analyzed"),), active_project_refs=("hydrotester",)) == ()


def test_secret_asset_is_not_analyzed():
    assert queue_asset_analysis((asset(sensitivity="credential_secret"),)) == ()


def test_stale_result_is_rejected():
    a = asset()
    result = AnalysisResult(asset_id="img-1", source_version_ref="v0", summary_ref="notion:summary", finding_refs=("finding:1",))
    assert "stale_analysis_result" in validate_analysis_result(result, a)
