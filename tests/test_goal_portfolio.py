from hypothesis import given, strategies as st

from nexus_core.goal_portfolio import GoalTrack, route_goal_portfolio, validate_goal_track


def goal(**overrides):
    values = dict(
        goal_ref="goal:ai-engineering",
        objective="Build demonstrable AI engineering capability through real NEXUS code and tests.",
        success_signal="A tested implementation, reviewable artifact or measured skill milestone is produced.",
        failure_signal="The cycle produces passive study only, duplicate architecture or no evidence-backed improvement.",
        horizon="quarter",
        state="next_action",
        next_action_ref="github:pr:13",
    )
    values.update(overrides)
    return GoalTrack(**values)


def test_next_action_goal_routes_ready():
    portfolio = route_goal_portfolio((goal(),))
    assert [item.goal_ref for item in portfolio.ready] == ["goal:ai-engineering"]
    assert portfolio.invalid == ()


def test_every_state_requires_exactly_its_routing_field():
    blocked = goal(goal_ref="goal:hydrotester", state="waiting_blocked", next_action_ref=None, blocker_ref="engineering:confirm-120mpa-scope")
    review = goal(goal_ref="goal:english", state="scheduled_review", next_action_ref=None, review_at="2026-08-20T20:00:00+03:30")
    paused = goal(goal_ref="goal:brand", state="explicit_pause", next_action_ref=None, pause_reason="Commercial and AI-engineering streams have higher current value.")
    portfolio = route_goal_portfolio((blocked, review, paused))
    assert [item.goal_ref for item in portfolio.blocked] == ["goal:hydrotester"]
    assert [item.goal_ref for item in portfolio.review] == ["goal:english"]
    assert [item.goal_ref for item in portfolio.paused] == ["goal:brand"]
    assert portfolio.invalid == ()


def test_ambiguous_goal_routing_fails_closed():
    assert "next_action state cannot carry blocker/review/pause routing" in validate_goal_track(goal(blocker_ref="blocker:should-not-coexist"))


def test_scheduled_review_requires_timezone():
    malformed = goal(state="scheduled_review", next_action_ref=None, review_at="2026-08-20T20:00:00")
    assert "review_at must include a timezone offset" in validate_goal_track(malformed)


def test_duplicate_goal_ref_is_invalid_in_same_cycle():
    portfolio = route_goal_portfolio((goal(), goal()))
    assert len(portfolio.ready) == 1
    assert len(portfolio.invalid) == 1
    assert "goal_ref must be unique within a portfolio cycle" in portfolio.invalid[0][1]


def test_invalid_goal_cannot_poison_later_valid_duplicate_ref():
    malformed = goal(goal_ref="goal:shared", blocker_ref="blocker:illegal-routing")
    valid = goal(goal_ref="goal:shared")
    portfolio = route_goal_portfolio((malformed, valid))
    assert [item.goal_ref for item in portfolio.ready] == ["goal:shared"]
    assert len(portfolio.invalid) == 1
    assert "next_action state cannot carry blocker/review/pause routing" in portfolio.invalid[0][1]
    assert "goal_ref must be unique within a portfolio cycle" not in portfolio.invalid[0][1]


def test_goal_metadata_rejects_unicode_format_controls():
    assert "goal_ref cannot contain control or formatting characters" in validate_goal_track(goal(goal_ref="goal:\u202eai"))


@given(st.one_of(st.none(), st.integers(), st.lists(st.integers()), st.dictionaries(st.text(max_size=5), st.integers(), max_size=3)))
def test_goal_validator_never_crashes_on_malformed_state(value):
    malformed = goal(state=value)  # type: ignore[arg-type]
    errors = validate_goal_track(malformed)
    assert errors
    assert "state must be supported" in errors


@given(st.text(min_size=1, max_size=32).filter(lambda text: text == text.strip() and "\x00" not in text))
def test_valid_goal_ref_survives_preceding_invalid_goal_with_same_ref(goal_ref):
    malformed = goal(goal_ref=goal_ref, blocker_ref="blocker:illegal-routing")
    valid = goal(goal_ref=goal_ref)
    portfolio = route_goal_portfolio((malformed, valid))
    if validate_goal_track(valid):
        assert not portfolio.ready
    else:
        assert [item.goal_ref for item in portfolio.ready] == [goal_ref]
