from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Sequence
from unicodedata import category


GoalState = Literal["next_action", "waiting_blocked", "scheduled_review", "explicit_pause"]
GoalHorizon = Literal["now", "quarter", "year", "long_term"]

_ALLOWED_STATES = {"next_action", "waiting_blocked", "scheduled_review", "explicit_pause"}
_ALLOWED_HORIZONS = {"now", "quarter", "year", "long_term"}
_MAX_META = 256
_MAX_TEXT = 1024
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


@dataclass(frozen=True)
class GoalTrack:
    goal_ref: str
    objective: str
    success_signal: str
    failure_signal: str
    horizon: GoalHorizon
    state: GoalState
    next_action_ref: str | None = None
    blocker_ref: str | None = None
    review_at: str | None = None
    pause_reason: str | None = None
    last_outcome_ref: str | None = None


@dataclass(frozen=True)
class GoalPortfolio:
    ready: tuple[GoalTrack, ...]
    blocked: tuple[GoalTrack, ...]
    review: tuple[GoalTrack, ...]
    paused: tuple[GoalTrack, ...]
    invalid: tuple[tuple[GoalTrack, tuple[str, ...]], ...]


def _text_error(name: str, value: object, max_len: int) -> str | None:
    if not isinstance(value, str): return f"{name} must be a string"
    if not value.strip(): return f"{name} is required"
    if value != value.strip(): return f"{name} cannot have leading or trailing whitespace"
    if len(value) > max_len: return f"{name} must be at most {max_len} characters"
    if any(category(ch) in _DISALLOWED_UNICODE_CATEGORIES for ch in value): return f"{name} cannot contain control or formatting characters"
    return None


def _optional_text_error(name: str, value: object, max_len: int) -> str | None:
    if value is None: return None
    return _text_error(name, value, max_len)


def _datetime_error(name: str, value: object) -> str | None:
    if value is None: return None
    text_error = _text_error(name, value, _MAX_META)
    if text_error: return text_error
    assert isinstance(value, str)
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return f"{name} must be ISO-8601"
    if parsed.tzinfo is None: return f"{name} must include a timezone offset"
    return None


def validate_goal_track(goal: GoalTrack) -> list[str]:
    if not isinstance(goal, GoalTrack): return ["goal must be a GoalTrack"]
    errors: list[str] = []
    for name, value, max_len in (("goal_ref", goal.goal_ref, _MAX_META), ("objective", goal.objective, _MAX_TEXT), ("success_signal", goal.success_signal, _MAX_TEXT), ("failure_signal", goal.failure_signal, _MAX_TEXT)):
        error = _text_error(name, value, max_len)
        if error: errors.append(error)
    if not isinstance(goal.horizon, str) or goal.horizon not in _ALLOWED_HORIZONS: errors.append("horizon must be supported")
    if not isinstance(goal.state, str) or goal.state not in _ALLOWED_STATES: errors.append("state must be supported")
    for name, value in (("next_action_ref", goal.next_action_ref), ("blocker_ref", goal.blocker_ref), ("pause_reason", goal.pause_reason), ("last_outcome_ref", goal.last_outcome_ref)):
        error = _optional_text_error(name, value, _MAX_TEXT)
        if error: errors.append(error)
    review_error = _datetime_error("review_at", goal.review_at)
    if review_error: errors.append(review_error)
    if goal.state == "next_action":
        if goal.next_action_ref is None: errors.append("next_action state requires next_action_ref")
        if any(value is not None for value in (goal.blocker_ref, goal.review_at, goal.pause_reason)): errors.append("next_action state cannot carry blocker/review/pause routing")
    elif goal.state == "waiting_blocked":
        if goal.blocker_ref is None: errors.append("waiting_blocked state requires blocker_ref")
        if any(value is not None for value in (goal.next_action_ref, goal.review_at, goal.pause_reason)): errors.append("waiting_blocked state cannot carry next-action/review/pause routing")
    elif goal.state == "scheduled_review":
        if goal.review_at is None: errors.append("scheduled_review state requires review_at")
        if any(value is not None for value in (goal.next_action_ref, goal.blocker_ref, goal.pause_reason)): errors.append("scheduled_review state cannot carry next-action/blocker/pause routing")
    elif goal.state == "explicit_pause":
        if goal.pause_reason is None: errors.append("explicit_pause state requires pause_reason")
        if any(value is not None for value in (goal.next_action_ref, goal.blocker_ref, goal.review_at)): errors.append("explicit_pause state cannot carry next-action/blocker/review routing")
    return errors


def route_goal_portfolio(goals: Sequence[GoalTrack]) -> GoalPortfolio:
    ready: list[GoalTrack] = []; blocked: list[GoalTrack] = []; review: list[GoalTrack] = []; paused: list[GoalTrack] = []; invalid: list[tuple[GoalTrack, tuple[str, ...]]] = []; seen: set[str] = set()
    for goal in goals:
        errors = validate_goal_track(goal)
        if isinstance(goal, GoalTrack) and isinstance(goal.goal_ref, str):
            if goal.goal_ref in seen: errors.append("goal_ref must be unique within a portfolio cycle")
            seen.add(goal.goal_ref)
        if errors:
            invalid.append((goal, tuple(errors))); continue
        if goal.state == "next_action": ready.append(goal)
        elif goal.state == "waiting_blocked": blocked.append(goal)
        elif goal.state == "scheduled_review": review.append(goal)
        else: paused.append(goal)
    return GoalPortfolio(tuple(ready), tuple(blocked), tuple(review), tuple(paused), tuple(invalid))
