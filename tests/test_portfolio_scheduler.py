from datetime import datetime, timedelta, timezone

from nexus_core.portfolio_scheduler import GoalLane, GoalWork, schedule_portfolio


NOW = datetime(2026, 8, 19, 20, 30, tzinfo=timezone.utc)


def work(i: str, lane: GoalLane, **kw) -> GoalWork:
    data = dict(
        work_id=i,
        goal_ref=f"goal:{i}",
        lane=lane,
        value=3,
        urgency=3,
        blocker=False,
        revenue_linked=False,
        evidence_strength=3,
        estimated_cost=1,
        last_progress_at=NOW - timedelta(hours=2),
        runnable=True,
    )
    data.update(kw)
    return GoalWork(**data)


def test_blocker_and_revenue_work_rank_first():
    decision = schedule_portfolio((
        work("research", GoalLane.RESEARCH, value=5),
        work("revenue", GoalLane.COMMERCIAL, revenue_linked=True),
        work("blocker", GoalLane.ENGINEERING, blocker=True),
    ), now=NOW, max_parallel=3)
    assert [x.work_id for x in decision.selected][:2] == ["blocker", "revenue"]


def test_lane_capacity_prevents_one_lane_monopoly():
    items = tuple(work(f"c{i}", GoalLane.COMMERCIAL, blocker=True, urgency=5) for i in range(4)) + (
        work("security", GoalLane.SECURITY, last_progress_at=NOW - timedelta(days=2)),
    )
    decision = schedule_portfolio(items, now=NOW, max_parallel=3, max_per_lane=2)
    assert sum(x.lane is GoalLane.COMMERCIAL for x in decision.selected) == 2
    assert any(x.work_id == "security" for x in decision.selected)


def test_starvation_guard_promotes_compounding_work():
    items = (
        work("fresh_network", GoalLane.NETWORK, urgency=4, value=4),
        work("starved_backup", GoalLane.BACKUP_RECOVERY, last_progress_at=NOW - timedelta(days=3), urgency=2, value=2),
    )
    decision = schedule_portfolio(items, now=NOW, max_parallel=1)
    assert decision.selected[0].work_id == "starved_backup"


def test_invalid_or_non_runnable_work_fails_closed():
    invalid = work("bad", GoalLane.RESEARCH, value=9)
    blocked = work("blocked", GoalLane.COMMERCIAL, runnable=False)
    decision = schedule_portfolio((invalid, blocked), now=NOW)
    assert not decision.selected
    assert {x.work_id for x in decision.deferred} == {"bad", "blocked"}


def test_duplicate_work_ids_do_not_both_execute():
    a = work("dup", GoalLane.RESEARCH)
    b = work("dup", GoalLane.NETWORK)
    decision = schedule_portfolio((a, b), now=NOW, max_parallel=5)
    assert len([x for x in decision.selected if x.work_id == "dup"]) == 1
    assert any("duplicate_work_id" in reason for reason in decision.reasons)
