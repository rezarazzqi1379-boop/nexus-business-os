import pytest
from outcome_manager import *
def O(i,**kw):
 d=dict(outcome_id=i,project_id="CHAIN",objective="convert buyer",bottleneck="demand",evidence_strength=.8,expected_value=.8,conversion_lift=.6,cost=.2,risk=.2); d.update(kw); return Outcome(**d)
def test_contradiction_blocks_even_high_value():
 x=O("x",contradiction=True,expected_value=1)
 assert state(x)==OutcomeState.BLOCKED and priority(x)==-1
def test_protected_action_never_wins_priority():
 assert priority(O("x",protected_action=True))==-1
def test_critical_unknown_forces_verification():
 assert state(O("x",critical_unknowns=1))==OutcomeState.VERIFY
def test_value_not_activity_drives_rank():
 high=O("vertical",expected_value=.9,conversion_lift=.9,cost=.2)
 noisy=O("more-leads",expected_value=.4,conversion_lift=.1,cost=.8)
 assert rank_outcomes((noisy,high))[0].outcome_id=="vertical"
def test_duplicate_outcome_rejected():
 with pytest.raises(ValueError): rank_outcomes((O("x"),O("x")))
def test_invalid_metric_rejected():
 with pytest.raises(ValueError): priority(O("x",risk=2))
