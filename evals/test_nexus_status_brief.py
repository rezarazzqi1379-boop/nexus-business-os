from pathlib import Path

from nexus_status_brief import (
    count_pending_approvals,
    count_pending_opportunities,
    group_projects_by_status,
    render_persian_brief,
)
from projects import ProjectPolicy


def _sample_projects():
    return {
        "a": ProjectPolicy("a", "active", 90, "Do A", ("ev1",)),
        "b": ProjectPolicy("b", "hold", 10, "Preserve B", (), ("outreach",)),
        "c": ProjectPolicy("c", "active", 50, "Do C", ()),
    }


def test_group_projects_orders_by_status_then_priority():
    grouped = group_projects_by_status(_sample_projects())
    statuses = [g.status for g in grouped]
    assert statuses.index("active") < statuses.index("hold")
    active_bucket = next(g for g in grouped if g.status == "active")
    assert [p.project_id for p in active_bucket.projects] == ["a", "c"]


def test_count_pending_opportunities_none_when_no_db(tmp_path):
    assert count_pending_opportunities(tmp_path / "does_not_exist.db") is None


def test_count_pending_approvals_none_when_no_db(tmp_path):
    assert count_pending_approvals(tmp_path / "does_not_exist.db") is None


def test_count_pending_opportunities_counts_real_drafts(tmp_path):
    import opportunity_suggestion_engine as ose
    from fal_vertical import LANE_FAL_A, PROJECT_ID
    from need_radar import NeedEvidence, NeedSignal

    db_path = tmp_path / "opportunities.db"
    queue = ose.OpportunityQueue(db_path)
    signal = NeedSignal(
        signal_id="s1", company_id="c1", company_name="Acme", company_role="buyer",
        project_id=PROJECT_ID, signal_type="procurement_request", need_hypothesis="Needs X",
        fit="strong", timing="current", relationship="warm_referral",
        evidence=(NeedEvidence("ev1", "FACT", "official", "ref1", "2026-09-14T00:00:00+00:00", "stmt"),),
    )
    queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=signal)
    assert count_pending_opportunities(db_path) == 1


def test_render_persian_brief_includes_project_ids():
    brief = render_persian_brief(projects=_sample_projects())
    assert "a" in brief
    assert "b" in brief
    assert "خلاصهٔ وضعیت NEXUS" in brief


def test_render_persian_brief_handles_missing_dbs_gracefully(tmp_path):
    brief = render_persian_brief(
        opportunities_db=tmp_path / "missing.db",
        approvals_db=tmp_path / "missing2.db",
        projects=_sample_projects(),
    )
    assert "در انتظار تصمیم انسانی" not in brief
