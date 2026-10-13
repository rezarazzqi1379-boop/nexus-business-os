import pytest
from commercial_outcome_measurement import Funnel,rates,compare

def test_activity_volume_alone_does_not_prove_improvement():
 b=Funnel(100,20,10,4,2,1,1,1000,("crm:b",))
 c=Funnel(200,40,20,8,4,2,2,1000,("crm:c",))
 r=compare(b,c)
 assert r["state"]=="MEASURED" and not r["improved"]

def test_missing_outcome_evidence_blocks_improvement_claim():
 b=Funnel(10,5,4,2,1,1,0)
 c=Funnel(10,6,4,3,2,1,1)
 assert compare(b,c)["state"]=="INSUFFICIENT_OUTCOME_EVIDENCE"

def test_conversion_gain_can_be_measured_with_evidence():
 b=Funnel(100,20,10,2,1,1,0,0,("crm:b",))
 c=Funnel(100,25,10,4,2,1,0,0,("crm:c",))
 r=compare(b,c)
 assert r["improved"] and r["rate_deltas"]["rfq"]>0

def test_non_monotonic_funnel_rejected():
 with pytest.raises(ValueError,match="non_monotonic_funnel"):
  rates(Funnel(10,11,0,0,0,0,0))
