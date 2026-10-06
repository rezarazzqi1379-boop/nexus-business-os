import pytest
from sales_readiness import *

def test_unknown_blocks_overall_ready():
 assert overall_readiness({"TECHNICAL":"READY","COMMERCIAL":"READY","COMPLIANCE":"UNKNOWN","CONTACT":"READY"})=="UNKNOWN"

def test_blocked_dominates():
 assert overall_readiness({"TECHNICAL":"PARTIAL","COMMERCIAL":"READY","COMPLIANCE":"BLOCKED","CONTACT":"UNKNOWN"})=="BLOCKED"

def test_all_ready():
 assert overall_readiness({k:"READY" for k in DIMENSIONS})=="READY"

def test_missing_dimension_invalid():
 with pytest.raises(ValueError):overall_readiness({"TECHNICAL":"READY"})
