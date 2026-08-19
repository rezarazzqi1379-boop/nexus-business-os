from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence

from nexus_core.goal_portfolio import GoalTrack

RiskLevel = Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True)
class DiagnosticFinding:
    finding_id: str
    risk: RiskLevel
    subject_ref: str
    condition: str
    evidence_refs: tuple[str, ...]
    recommended_action: str


def diagnose_goal_portfolio(goals: Sequence[GoalTrack], *, now: str) -> tuple[DiagnosticFinding, ...]:
    current = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if current.tzinfo is None:
        raise ValueError("now must include a timezone offset")
    findings: list[DiagnosticFinding] = []
    for goal in goals:
        if goal.state == "waiting_blocked" and goal.blocker_ref:
            findings.append(DiagnosticFinding(
                finding_id=f"blocked:{goal.goal_ref}", risk="high", subject_ref=goal.goal_ref,
                condition="Goal is blocked and may propagate delay to dependent goals.",
                evidence_refs=(goal.blocker_ref,),
                recommended_action="Verify blocker freshness and downstream dependencies; resolve, reroute or explicitly pause.",
            ))
        elif goal.state == "scheduled_review" and goal.review_at:
            review = datetime.fromisoformat(goal.review_at.replace("Z", "+00:00"))
            if review.tzinfo is None:
                continue
            if review <= current:
                findings.append(DiagnosticFinding(
                    finding_id=f"overdue-review:{goal.goal_ref}", risk="medium", subject_ref=goal.goal_ref,
                    condition="Scheduled review is due or overdue.", evidence_refs=(goal.review_at,),
                    recommended_action="Run the review and route the goal to next_action, waiting_blocked or explicit_pause.",
                ))
        if goal.state == "next_action" and not goal.last_outcome_ref:
            findings.append(DiagnosticFinding(
                finding_id=f"no-outcome-history:{goal.goal_ref}", risk="low", subject_ref=goal.goal_ref,
                condition="Active goal has no recorded measurable outcome yet.", evidence_refs=(goal.next_action_ref or goal.goal_ref,),
                recommended_action="Require the next cycle to produce a measurable outcome or downgrade the loop.",
            ))
    return tuple(findings)
