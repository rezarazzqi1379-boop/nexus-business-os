import pytest
from nexus_simulation import SimulationCase, evaluate_case, run_fixture

def case(**changes):
    d=dict(case_id="fixture-1",expected_project="SANDBOX",observed_project="SANDBOX",
           source_locator="synthetic:source",identity_reviewed=True,need_verified=True)
    d.update(changes)
    return SimulationCase(**d)

def test_positive_case_reaches_human_review_only():
    assert evaluate_case(case()) == ("HUMAN_REVIEW", ())

def test_cross_project_is_blocked():
    assert "cross_project_or_missing_scope" in evaluate_case(case(observed_project="OTHER"))[1]

def test_missing_source_is_blocked():
    assert "missing_source" in evaluate_case(case(source_locator=""))[1]

def test_unreviewed_identity_is_blocked():
    assert "unreviewed_identity" in evaluate_case(case(identity_reviewed=False))[1]

def test_unverified_need_is_blocked():
    assert "unverified_need" in evaluate_case(case(need_verified=False))[1]

def test_external_action_is_never_authorized():
    assert "external_action_blocked" in evaluate_case(case(external_action_requested=True))[1]

def test_deterministic_fixture_aggregate():
    x=run_fixture((case(),case(case_id="fixture-2",observed_project="OTHER")))
    assert x["fixture_count"]==2 and x["human_review"]==1
    assert x["research_only"]==1 and x["external_actions_authorized"]==0

def test_duplicate_fixture_id_rejected():
    with pytest.raises(ValueError,match="duplicate_case_id"):
        run_fixture((case(),case()))
