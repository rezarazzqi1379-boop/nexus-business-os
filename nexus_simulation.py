"""Deterministic simulation for cross-project evidence and action-gate invariants.

Synthetic fixtures only; this is not a background runner or production agent.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class SimulationCase:
    case_id: str
    expected_project: str
    observed_project: str
    source_locator: str
    identity_reviewed: bool
    need_verified: bool
    external_action_requested: bool = False

def evaluate_case(case: SimulationCase) -> tuple[str, tuple[str, ...]]:
    errors = []
    if not case.expected_project or case.expected_project != case.observed_project:
        errors.append("cross_project_or_missing_scope")
    if not case.source_locator.strip():
        errors.append("missing_source")
    if not case.identity_reviewed:
        errors.append("unreviewed_identity")
    if not case.need_verified:
        errors.append("unverified_need")
    if case.external_action_requested:
        errors.append("external_action_blocked")
    return ("RESEARCH_ONLY" if errors else "HUMAN_REVIEW", tuple(errors))

def run_fixture(cases: tuple[SimulationCase, ...]) -> dict:
    if len({x.case_id for x in cases}) != len(cases):
        raise ValueError("duplicate_case_id")
    results = tuple((c.case_id, *evaluate_case(c)) for c in cases)
    return {"fixture_count": len(cases),
            "human_review": sum(x[1] == "HUMAN_REVIEW" for x in results),
            "research_only": sum(x[1] == "RESEARCH_ONLY" for x in results),
            "external_actions_authorized": 0,
            "results": results}
