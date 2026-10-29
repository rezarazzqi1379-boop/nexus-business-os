from copy import deepcopy
from pathlib import Path
import json
import pytest
from verify_source_trial import audit


def proof():
    return json.loads((Path(__file__).parents[1]/"evidence/source-monitor-trial-20261029.json").read_text(encoding="utf-8"))


def test_actual_finite_trial_is_partial_and_budget_bounded():
    result = audit(proof())
    assert result["reserved_attempts"] == 6 and result["responses_with_evidence"] == 6
    assert not result["clean_three_tick_collection_proven"]
    assert (2,"ted") in result["nonempty_collection_pairs"]


@pytest.mark.parametrize("change",["budget","scope","source","duplicate","time"])
def test_proof_tampering_rejected(change):
    data = deepcopy(proof())
    if change == "budget":
        data["attempts"].append(data["attempts"][0])
    elif change == "scope":
        data["evidence"][0]["project_id"] = "other"
    elif change == "source":
        data["evidence"][0]["source_url"] = "https://evil.invalid"
    elif change == "duplicate":
        data["evidence"].append(data["evidence"][0])
    else:
        data["attempts"][0]["reserved_at"] = "2026-10-28T00:00:00+00:00"
    with pytest.raises(AssertionError):
        audit(data)
