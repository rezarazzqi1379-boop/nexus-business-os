from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

EvalClass = Literal["CANONICAL", "SECURITY", "PROJECT_ISOLATION", "DYNAMIC_FRESHNESS", "AUTONOMY", "OUTCOME"]
Verdict = Literal["PASS", "FAIL", "INVALID"]


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    eval_class: EvalClass
    project_id: str
    prompt: str
    expected_rules: tuple[str, ...]
    forbidden_rules: tuple[str, ...]
    source_refs: tuple[str, ...]
    frozen_version: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("case_id", "project_id", "prompt", "frozen_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        if not self.expected_rules:
            errors.append("expected_rules required")
        if len(set(self.source_refs)) != len(self.source_refs):
            errors.append("duplicate source_refs")
        if set(self.expected_rules) & set(self.forbidden_rules):
            errors.append("rule cannot be both expected and forbidden")
        return tuple(errors)


@dataclass(frozen=True)
class EvalObservation:
    case_id: str
    satisfied_rules: tuple[str, ...]
    violated_rules: tuple[str, ...]
    project_id: str
    source_refs_used: tuple[str, ...]
    human_corrections: int = 0


@dataclass(frozen=True)
class EvalResult:
    verdict: Verdict
    reasons: tuple[str, ...]


def evaluate_case(case: EvalCase, obs: EvalObservation) -> EvalResult:
    errors = list(case.validate())
    if case.case_id != obs.case_id:
        errors.append("case identity mismatch")
    if case.project_id != obs.project_id:
        errors.append("cross-project contamination")
    if obs.human_corrections < 0:
        errors.append("human_corrections must be non-negative")
    if not set(obs.source_refs_used).issubset(set(case.source_refs)):
        errors.append("unapproved source reference used")
    if errors:
        return EvalResult("INVALID", tuple(errors))

    reasons: list[str] = []
    missing = sorted(set(case.expected_rules) - set(obs.satisfied_rules))
    if missing:
        reasons.append("missing required rules: " + ", ".join(missing))
    forbidden_hit = sorted(set(case.forbidden_rules) & (set(obs.satisfied_rules) | set(obs.violated_rules)))
    if forbidden_hit:
        reasons.append("forbidden rules triggered: " + ", ".join(forbidden_hit))
    if obs.violated_rules:
        reasons.append("violations: " + ", ".join(sorted(set(obs.violated_rules))))
    if reasons:
        return EvalResult("FAIL", tuple(reasons))
    return EvalResult("PASS", ("all frozen acceptance rules satisfied",))


def corpus_is_valid(cases: Sequence[EvalCase]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for case in cases:
        errors.extend(f"{case.case_id}: {e}" for e in case.validate())
        if case.case_id in seen:
            errors.append(f"duplicate case_id: {case.case_id}")
        seen.add(case.case_id)
    return tuple(errors)
