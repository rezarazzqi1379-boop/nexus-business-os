from dataclasses import replace

from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from nexus_core.goal_portfolio import GoalTrack, route_goal_portfolio


class GoalPortfolioStateMachine(RuleBasedStateMachine):
    """Model repeated GoalTrack routing changes as generated operation sequences.

    This test is intentionally stateful: Hypothesis chooses not only values but the
    sequence of state transitions. The invariant checks that a single goal is always
    routed into exactly one canonical queue when structurally valid, and into no live
    queue when we deliberately introduce ambiguous routing metadata.
    """

    def __init__(self) -> None:
        super().__init__()
        self.goal = GoalTrack(
            goal_ref="goal:stateful",
            objective="Keep one goal deterministically routed across repeated state changes.",
            success_signal="Every valid transition lands in exactly one canonical portfolio queue.",
            failure_signal="Ambiguous or malformed routing becomes live state instead of failing closed.",
            horizon="quarter",
            state="next_action",
            next_action_ref="action:initial",
        )
        self.expected_queue = "ready"

    @rule()
    def route_next_action(self) -> None:
        self.goal = replace(
            self.goal,
            state="next_action",
            next_action_ref="action:generated",
            blocker_ref=None,
            review_at=None,
            pause_reason=None,
        )
        self.expected_queue = "ready"

    @rule()
    def route_waiting_blocked(self) -> None:
        self.goal = replace(
            self.goal,
            state="waiting_blocked",
            next_action_ref=None,
            blocker_ref="blocker:generated",
            review_at=None,
            pause_reason=None,
        )
        self.expected_queue = "blocked"

    @rule()
    def route_scheduled_review(self) -> None:
        self.goal = replace(
            self.goal,
            state="scheduled_review",
            next_action_ref=None,
            blocker_ref=None,
            review_at="2026-08-20T20:00:00+03:30",
            pause_reason=None,
        )
        self.expected_queue = "review"

    @rule()
    def route_explicit_pause(self) -> None:
        self.goal = replace(
            self.goal,
            state="explicit_pause",
            next_action_ref=None,
            blocker_ref=None,
            review_at=None,
            pause_reason="Generated pause for state-machine testing.",
        )
        self.expected_queue = "paused"

    @rule()
    def inject_ambiguous_routing(self) -> None:
        # A compromised/stale writer may leave routing fields from two states at once.
        # The portfolio must never guess which one wins; ambiguity is invalid state.
        self.goal = replace(
            self.goal,
            state="next_action",
            next_action_ref="action:ambiguous",
            blocker_ref="blocker:must-fail-closed",
            review_at=None,
            pause_reason=None,
        )
        self.expected_queue = "invalid"

    @invariant()
    def goal_is_never_live_in_multiple_queues(self) -> None:
        portfolio = route_goal_portfolio((self.goal,))
        live_counts = {
            "ready": len(portfolio.ready),
            "blocked": len(portfolio.blocked),
            "review": len(portfolio.review),
            "paused": len(portfolio.paused),
        }

        if self.expected_queue == "invalid":
            assert sum(live_counts.values()) == 0
            assert len(portfolio.invalid) == 1
            return

        assert len(portfolio.invalid) == 0
        assert live_counts[self.expected_queue] == 1
        assert sum(live_counts.values()) == 1


TestGoalPortfolioStateMachine = GoalPortfolioStateMachine.TestCase
