from nexus_core.goal_portfolio import GoalTrack
from nexus_core.predictive_diagnostics import diagnose_goal_portfolio


def test_blocked_goal_emits_high_risk_finding():
    goal = GoalTrack(
        goal_ref="goal:hydrotester", objective="Resolve hydrotester requirements.",
        success_signal="Engineering requirement is verified.", failure_signal="Requirement remains unknown.",
        horizon="now", state="waiting_blocked", blocker_ref="engineering:120mpa-scope",
    )
    findings = diagnose_goal_portfolio((goal,), now="2026-08-19T21:00:00+03:30")
    assert findings[0].risk == "high"
    assert findings[0].subject_ref == "goal:hydrotester"


def test_overdue_review_is_detected():
    goal = GoalTrack(
        goal_ref="goal:english", objective="Improve spoken English.",
        success_signal="Speaking practice completed and reviewed.", failure_signal="No practice evidence.",
        horizon="quarter", state="scheduled_review", review_at="2026-08-19T20:00:00+03:30",
    )
    findings = diagnose_goal_portfolio((goal,), now="2026-08-19T21:00:00+03:30")
    assert any(f.finding_id == "overdue-review:goal:english" for f in findings)


def test_active_goal_without_outcome_history_is_flagged():
    goal = GoalTrack(
        goal_ref="goal:ai-engineering", objective="Build demonstrable AI engineering skill.",
        success_signal="A tested artifact is produced.", failure_signal="Only passive study occurs.",
        horizon="quarter", state="next_action", next_action_ref="github:pr:13",
    )
    findings = diagnose_goal_portfolio((goal,), now="2026-08-19T21:00:00+03:30")
    assert any(f.finding_id == "no-outcome-history:goal:ai-engineering" for f in findings)


def test_timezone_is_required_for_diagnostic_clock():
    goal = GoalTrack(
        goal_ref="goal:test", objective="Test.", success_signal="Pass.", failure_signal="Fail.",
        horizon="now", state="explicit_pause", pause_reason="No current value.",
    )
    try:
        diagnose_goal_portfolio((goal,), now="2026-08-19T21:00:00")
        assert False
    except ValueError as exc:
        assert "timezone" in str(exc)
