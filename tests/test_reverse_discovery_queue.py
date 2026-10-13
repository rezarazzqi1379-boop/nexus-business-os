import pytest
from reverse_discovery_queue import *

def test_information_value_priority_controls_queue():
 low=DiscoveryTask("low","q","UPSTREAM",1,1,1,1,1,10)
 high=DiscoveryTask("high","q","DOWNSTREAM",2,1,1,1,1,1)
 assert prioritize((low,high))[0].task_id=="high"

def test_missing_node_generation_covers_both_directions_and_falsification():
 xs=missing_node_tasks(source_id="ore_importer",target_id="steel_mill",relation="SUPPLIED_TO")
 assert {x.path for x in xs}=={"UPSTREAM","INTERMEDIATE","DOWNSTREAM","FALSIFICATION"}

def test_zero_cost_does_not_create_infinite_priority():
 with pytest.raises(ValueError):DiscoveryTask("x","q","p",1,1,1,1,1,0).priority()
