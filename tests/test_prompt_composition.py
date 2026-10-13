import pytest
from prompt_composition import *
def D(k,v,s,p,proj=""): return Directive(k,v,s,p,proj)
def test_canonical_beats_adapter():
 out,c=compose((D("freshness","cached","Exa",Priority.ADAPTER),D("freshness","live","Master",Priority.CANONICAL)),"P")
 assert out["freshness"]=="live" and c[0].winner=="Master"
def test_action_gate_beats_capability():
 out,_=compose((D("send","yes","Sales",Priority.CAPABILITY),D("send","approval_required","Gate",Priority.ACTION_GATE)),"P")
 assert out["send"]=="approval_required"
def test_cross_project_project_directive_fails_closed():
 with pytest.raises(ValueError): compose((D("spec","A","P1 master",Priority.PROJECT,"P1"),D("spec","B","P2 master",Priority.PROJECT,"P2")),"P1")
def test_equal_priority_conflict_is_not_silently_resolved():
 with pytest.raises(ValueError): compose((D("mode","a","cap1",Priority.CAPABILITY),D("mode","b","cap2",Priority.CAPABILITY)),"P")
def test_prompt_not_promoted_for_costly_no_better_variant():
 b=(PromptMetric("x","1","t",True,cost_units=1,conversion_delta=1),)
 c=(PromptMetric("x","2","t",True,cost_units=2,conversion_delta=1),)
 assert not should_promote(c,b)
def test_prompt_promotes_only_measured_improvement():
 b=(PromptMetric("x","1","a",False,failures=1,cost_units=2),PromptMetric("x","1","b",True,cost_units=2))
 c=(PromptMetric("x","2","a",True,cost_units=1,conversion_delta=1),PromptMetric("x","2","b",True,cost_units=1))
 assert should_promote(c,b)
