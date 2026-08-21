import pytest

from nexus_autonomy.opportunity_loop import OpportunityCandidate, candidates_to_work_items


def test_candidate_becomes_research_only_work():
    (item,) = candidates_to_work_items(
        [OpportunityCandidate("kcl-buyer-1", "Qualify a possible KCl buyer", ("source:1",), value="high")],
        acceptable_capability_ids=("web-research",),
    )
    assert item.task_id == "opportunity:kcl-buyer-1"
    assert item.action_kind == "research"
    assert item.write_required is False
    assert item.reversible is True
    assert item.goal_ref == "opportunity:kcl-buyer-1"


def test_missing_evidence_is_rejected():
    with pytest.raises(ValueError, match="requires retrievable evidence"):
        candidates_to_work_items(
            [OpportunityCandidate("x", "Investigate x", ())],
            acceptable_capability_ids=("web-research",),
        )


def test_duplicate_candidates_are_rejected():
    candidates = [
        OpportunityCandidate("x", "First", ("ref:1",)),
        OpportunityCandidate("x", "Second", ("ref:2",)),
    ]
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        candidates_to_work_items(candidates, acceptable_capability_ids=("web-research",))


def test_missing_capability_contract_is_rejected():
    with pytest.raises(ValueError, match="acceptable_capability_ids"):
        candidates_to_work_items([], acceptable_capability_ids=())
