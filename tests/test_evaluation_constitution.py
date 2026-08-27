import json
from pathlib import Path

from nexus_core.evaluation_constitution import EvalCase, EvalObservation, corpus_is_valid, evaluate_case


def _load_cases():
    raw = json.loads(Path("data/evals/frozen_benchmark_corpus_v0.1.json").read_text())
    cases = []
    for item in raw["cases"]:
        cases.append(EvalCase(
            case_id=item["case_id"],
            eval_class=item["class"],
            project_id=item["project_id"],
            prompt=item["prompt"],
            expected_rules=tuple(item["expected_rules"]),
            forbidden_rules=tuple(item["forbidden_rules"]),
            source_refs=tuple(item["source_refs"]),
            frozen_version=raw["schema_version"],
        ))
    return tuple(cases)


def test_frozen_corpus_is_valid_and_cross_domain():
    cases = _load_cases()
    assert not corpus_is_valid(cases)
    assert len(cases) >= 7
    assert {c.project_id for c in cases} >= {"PRJ-HYD-01", "PRJ-KCL-01", "PRJ-HTL-01", "PRJ-CAN-01", "NEXUS_CORE"}


def test_perfect_observation_passes():
    case = _load_cases()[0]
    obs = EvalObservation(case.case_id, case.expected_rules, (), case.project_id, case.source_refs)
    assert evaluate_case(case, obs).verdict == "PASS"


def test_cross_project_contamination_is_invalid():
    case = _load_cases()[0]
    obs = EvalObservation(case.case_id, case.expected_rules, (), "PRJ-KCL-01", case.source_refs)
    result = evaluate_case(case, obs)
    assert result.verdict == "INVALID"
    assert any("cross-project" in r for r in result.reasons)


def test_unapproved_source_use_is_invalid():
    case = _load_cases()[1]
    obs = EvalObservation(case.case_id, case.expected_rules, (), case.project_id, case.source_refs + ("PRJ-HYD-01-ENG:v1.1",))
    assert evaluate_case(case, obs).verdict == "INVALID"


def test_missing_rule_fails():
    case = _load_cases()[4]
    obs = EvalObservation(case.case_id, case.expected_rules[:-1], (), case.project_id, case.source_refs)
    assert evaluate_case(case, obs).verdict == "FAIL"


def test_forbidden_rule_never_passes():
    case = _load_cases()[6]
    obs = EvalObservation(case.case_id, case.expected_rules + (case.forbidden_rules[0],), (), case.project_id, case.source_refs)
    assert evaluate_case(case, obs).verdict == "FAIL"
