import pytest
from prompt_os import *
def test_dynamic_facts_never_baked_into_prompt_os():
 assert not prompt_may_embed_dynamic_fact()
def test_router_requires_project_and_capability():
 with pytest.raises(ValueError): route_prompt(PromptRequest(project_id="",capability="research"))
def test_dynamic_fact_forces_live_refresh():
 with pytest.raises(ValueError): route_prompt(PromptRequest(project_id="P",capability="sales",dynamic_fact_required=True))
def test_adapter_is_layer_not_authority():
 r=route_prompt(PromptRequest(project_id="P",capability="research",adapter="Exa",live_evidence_refreshed=True))
 assert r==("NEXUS_KERNEL","CAPABILITY:research","ADAPTER:Exa","PROJECT:P","EVAL:SELF_CHECK")
def test_protected_action_gets_gate():
 assert route_prompt(PromptRequest(project_id="P",capability="email",protected_action=True))[-1]=="GATE:HUMAN_APPROVAL"
def test_prompt_activation_requires_test_and_measurement():
 p=PromptSpec("x","1",PromptLayer.CAPABILITY,"do x","fixture",active=False)
 assert not may_activate(p,True,False)
 assert may_activate(p,True,True)
