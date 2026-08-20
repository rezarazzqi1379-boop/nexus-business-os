from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence

from nexus_core.capability_health import CapabilityHealth, diagnose_capability_health
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


def diagnose_capability_routes(
    records: Sequence[CapabilityHealth],
    *,
    now: str,
    max_age_seconds: int = 21_600,
) -> tuple[DiagnosticFinding, ...]:
    current = datetime.fromisoformat(now.replace("Z", "+00:00"))
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must include a timezone offset")

    translated: list[DiagnosticFinding] = []
    for finding in diagnose_capability_health(records, now=current, max_age_seconds=max_age_seconds):
        risk: RiskLevel
        if finding.severity == "block":
            risk = "high"
        elif finding.severity == "warning":
            risk = "medium"
        else:
            risk = "low"

        record = next((item for item in records if isinstance(item, CapabilityHealth) and item.capability_id == finding.capability_id), None)
        evidence_refs = (record.evidence_ref,) if record is not None else (f"capability:{finding.capability_id}",)
        translated.append(DiagnosticFinding(
            finding_id=f"capability:{finding.code}:{finding.capability_id}",
            risk=risk,
            subject_ref=finding.capability_id,
            condition=finding.detail,
            evidence_refs=evidence_refs,
            recommended_action=(
                "Re-probe the exact route with a safe read-only health check before planning dependent work."
                if finding.code in {"stale_health_check", "future_health_check", "route_unverified"}
                else "Keep dependent work blocked, verify authentication/route/permission state, and do not infer capability from UI presence."
            ),
        ))
    return tuple(translated)
