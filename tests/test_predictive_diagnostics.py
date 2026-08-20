from nexus_core.capability_health import CapabilityHealth
from nexus_core.goal_portfolio import GoalTrack
from nexus_core.predictive_diagnostics import diagnose_capability_routes, diagnose_goal_portfolio


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


def test_stale_capability_route_becomes_predictive_finding():
    health = CapabilityHealth(
        capability_id="gmail.read",
        state="verified_read",
        checked_at="2026-08-19T10:00:00+00:00",
        route_ref="connector:gmail:list_labels",
        evidence_ref="probe:gmail:old",
        proven_access=("read",),
    )
    findings = diagnose_capability_routes((health,), now="2026-08-19T21:00:00+03:30")
    assert any(f.finding_id == "capability:stale_health_check:gmail.read" and f.risk == "medium" for f in findings)


def test_blocked_connector_becomes_high_risk_route_finding():
    health = CapabilityHealth(
        capability_id="openai.platform",
        state="blocked",
        checked_at="2026-08-19T18:20:00+00:00",
        route_ref="openai-platform:list-key-targets",
        evidence_ref="probe:openai-platform:provider-rejected",
        proven_access=(),
    )
    findings = diagnose_capability_routes((health,), now="2026-08-19T21:50:00+03:30")
    assert any(f.subject_ref == "openai.platform" and f.risk == "high" for f in findings)


def test_unverified_external_route_never_becomes_runtime_capability():
    health = CapabilityHealth(
        capability_id="zotero.local",
        state="not_available_here",
        checked_at="2026-08-19T18:20:00+00:00",
        route_ref="codex:zotero-local-api",
        evidence_ref="plugin-manager:not-installed-here",
        proven_access=(),
    )
    findings = diagnose_capability_routes((health,), now="2026-08-19T21:50:00+03:30")
    assert any(f.finding_id == "capability:route_unverified:zotero.local" for f in findings)
