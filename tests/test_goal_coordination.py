from nexus_core.goal_coordination import GoalLink, coordinate_goals
from nexus_core.goal_portfolio import GoalTrack


def goal(ref: str, state: str, **kwargs) -> GoalTrack:
    base = dict(
        goal_ref=ref,
        objective=f"Advance {ref}",
        success_signal="A measurable result is produced.",
        failure_signal="No measurable progress or a real blocker is found.",
        horizon="quarter",
        state=state,
        next_action_ref=None,
        blocker_ref=None,
        review_at=None,
        pause_reason=None,
    )
    if state == "next_action":
        base["next_action_ref"] = f"next:{ref}"
    elif state == "waiting_blocked":
        base["blocker_ref"] = f"blocker:{ref}"
    elif state == "scheduled_review":
        base["review_at"] = "2026-08-20T20:00:00+03:30"
    elif state == "explicit_pause":
        base["pause_reason"] = "Lower current value than active goals."
    base.update(kwargs)
    return GoalTrack(**base)


def test_blocked_source_propagates_dependency_blocker():
    goals = (goal("goal:hydrotester", "waiting_blocked"), goal("goal:commercial-revenue", "next_action"))
    result = coordinate_goals(
        goals,
        (GoalLink("goal:hydrotester", "goal:commercial-revenue", "blocks", "evidence:engineering-confirmation"),),
    )
    assert result.dependency_blocked == (("goal:commercial-revenue", "goal:hydrotester"),)


def test_competing_active_goals_surface_conflict_without_auto_reprioritization():
    goals = (goal("goal:commercial-revenue", "next_action"), goal("goal:personal-brand", "next_action"))
    result = coordinate_goals(
        goals,
        (GoalLink("goal:commercial-revenue", "goal:personal-brand", "competes", "policy:focus-budget"),),
    )
    assert result.active_conflicts == (("goal:commercial-revenue", "goal:personal-brand"),)


def test_support_link_is_recorded_even_when_target_is_not_active():
    goals = (goal("goal:english", "scheduled_review"), goal("goal:international-trade", "next_action"))
    result = coordinate_goals(
        goals,
        (GoalLink("goal:english", "goal:international-trade", "supports", "strategy:trade-language"),),
    )
    assert result.support_edges == (("goal:english", "goal:international-trade"),)


def test_unknown_or_self_links_fail_closed():
    goals = (goal("goal:ai-engineering", "next_action"),)
    result = coordinate_goals(
        goals,
        (
            GoalLink("goal:missing", "goal:ai-engineering", "supports", "evidence:x"),
            GoalLink("goal:ai-engineering", "goal:ai-engineering", "supports", "evidence:y"),
        ),
    )
    assert len(result.invalid_links) == 2


def test_duplicate_link_is_invalid():
    goals = (goal("goal:ai-engineering", "next_action"), goal("goal:nexus-product", "next_action"))
    link = GoalLink("goal:ai-engineering", "goal:nexus-product", "supports", "strategy:reuse-learning")
    result = coordinate_goals(goals, (link, link))
    assert len(result.support_edges) == 1
    assert len(result.invalid_links) == 1
