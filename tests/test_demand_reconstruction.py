import pytest
from demand_reconstruction import *

def test_finished_component_does_not_become_raw_material_purchase():
 s=DemandSignal("Mozyr Oil Refinery","GEAR","driving wheel 42CrMo4+QT",("tender:2026",),grade="42CrMo4+QT")
 x=infer_upstream(s,input_form="bar_or_forging",reason="manufacturing input may be required")
 assert x["state"]=="HYPOTHESIS" and not x["purchase_evidence"]

def test_observed_raw_bar_can_stay_raw_bar():
 s=DemandSignal("Buyer","RAW_BAR","round 70 mm",("tender:1",),grade="40HN2MA",quantity=1.5,quantity_unit="t")
 s.validate()

def test_demand_requires_evidence():
 with pytest.raises(ValueError):DemandSignal("B","RAW_BAR","x",()).validate()
