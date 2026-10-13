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


def test_partial_not_ready():
 assert overall_readiness({"TECHNICAL":"PARTIAL","COMMERCIAL":"PARTIAL","COMPLIANCE":"READY","CONTACT":"READY"})=="PARTIAL"


def test_contact_partial_cannot_make_overall_ready():
 assert overall_readiness({"TECHNICAL":"READY","COMMERCIAL":"READY","COMPLIANCE":"READY","CONTACT":"PARTIAL"})=="PARTIAL"

def test_unknown_compliance_dominates_named_contact():
 assert overall_readiness({"TECHNICAL":"PARTIAL","COMMERCIAL":"PARTIAL","COMPLIANCE":"UNKNOWN","CONTACT":"PARTIAL"})=="UNKNOWN"
