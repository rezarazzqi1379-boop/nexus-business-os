from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class TemporalFact:
    fact_id: str
    subject: str
    predicate: str
    value: str
    valid_from: datetime
    valid_to: datetime | None
    observed_at: datetime
    source_ref: str


def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def validate_temporal_fact(fact: TemporalFact) -> tuple[str, ...]:
    """Validate application-time and observation-time separately.

    A recently observed record is not necessarily the currently valid truth. NEXUS
    therefore tracks when a statement is valid in the world independently from
    when the system observed it.
    """
    errors: list[str] = []
    if not fact.fact_id.strip():
        errors.append("invalid_fact_id")
    if not fact.subject.strip() or not fact.predicate.strip() or not fact.value.strip():
        errors.append("invalid_statement")
    if not fact.source_ref.strip():
        errors.append("missing_source_ref")
    for name, value in (
        ("valid_from", fact.valid_from),
        ("observed_at", fact.observed_at),
    ):
        if not _aware(value):
            errors.append(f"{name}_must_be_timezone_aware")
    if fact.valid_to is not None:
        if not _aware(fact.valid_to):
            errors.append("valid_to_must_be_timezone_aware")
        elif fact.valid_to <= fact.valid_from:
            errors.append("invalid_validity_window")
    return tuple(errors)


def is_valid_at(fact: TemporalFact, when: datetime) -> bool:
    if validate_temporal_fact(fact) or not _aware(when):
        return False
    if when < fact.valid_from:
        return False
    return fact.valid_to is None or when < fact.valid_to


def current_facts(facts: tuple[TemporalFact, ...], *, now: datetime | None = None) -> tuple[TemporalFact, ...]:
    now = now or datetime.now(timezone.utc)
    return tuple(f for f in facts if is_valid_at(f, now))


def latest_observation(facts: tuple[TemporalFact, ...]) -> TemporalFact | None:
    valid = tuple(f for f in facts if not validate_temporal_fact(f))
    return max(valid, key=lambda f: f.observed_at, default=None)
