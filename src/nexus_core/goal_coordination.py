from dataclasses import dataclass
from typing import Literal, Sequence

from nexus_core.goal_portfolio import GoalTrack


LinkKind = Literal["supports", "blocks", "competes"]


@dataclass(frozen=True)
class GoalLink:
    source_goal_ref: str
    target_goal_ref: str
    kind: LinkKind
    rationale_ref: str


@dataclass(frozen=True)
class GoalCoordinationResult:
    dependency_blocked: tuple[tuple[str, str], ...]
    active_conflicts: tuple[tuple[str, str], ...]
    support_edges: tuple[tuple[str, str], ...]
    invalid_links: tuple[tuple[GoalLink, tuple[str, ...]], ...]


def validate_goal_link(link: GoalLink, known_goal_refs: set[str]) -> list[str]:
    if not isinstance(link, GoalLink):
        return ["link must be a GoalLink"]
    errors: list[str] = []
    if link.source_goal_ref not in known_goal_refs:
        errors.append("source_goal_ref must reference a known goal")
    if link.target_goal_ref not in known_goal_refs:
        errors.append("target_goal_ref must reference a known goal")
    if link.source_goal_ref == link.target_goal_ref:
        errors.append("goal link cannot self-reference")
    if link.kind not in {"supports", "blocks", "competes"}:
        errors.append("kind must be supported")
    if not isinstance(link.rationale_ref, str) or not link.rationale_ref.strip():
        errors.append("rationale_ref is required")
    return errors


def coordinate_goals(goals: Sequence[GoalTrack], links: Sequence[GoalLink]) -> GoalCoordinationResult:
    by_ref = {goal.goal_ref: goal for goal in goals if isinstance(goal, GoalTrack) and isinstance(goal.goal_ref, str)}
    known = set(by_ref)
    dependency_blocked: list[tuple[str, str]] = []
    active_conflicts: list[tuple[str, str]] = []
    support_edges: list[tuple[str, str]] = []
    invalid_links: list[tuple[GoalLink, tuple[str, ...]]] = []
    seen: set[tuple[str, str, str]] = set()

    for link in links:
        errors = validate_goal_link(link, known)
        key = (link.source_goal_ref, link.target_goal_ref, link.kind)
        if key in seen:
            errors.append("duplicate goal link in same coordination cycle")
        seen.add(key)
        if errors:
            invalid_links.append((link, tuple(errors)))
            continue
        source = by_ref[link.source_goal_ref]
        target = by_ref[link.target_goal_ref]
        if link.kind == "blocks" and source.state == "waiting_blocked":
            dependency_blocked.append((target.goal_ref, source.goal_ref))
        elif link.kind == "competes" and source.state == "next_action" and target.state == "next_action":
            pair = tuple(sorted((source.goal_ref, target.goal_ref)))
            if pair not in active_conflicts:
                active_conflicts.append(pair)
        elif link.kind == "supports":
            support_edges.append((source.goal_ref, target.goal_ref))

    return GoalCoordinationResult(
        tuple(dependency_blocked), tuple(active_conflicts), tuple(support_edges), tuple(invalid_links)
    )
