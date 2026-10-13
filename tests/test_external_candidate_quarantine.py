from external_candidate_quarantine import *
def test_code_execution_is_quarantined(): assert disposition(CandidateRisk("x",arbitrary_code=True))=="QUARANTINE_SANDBOX_ONLY"
def test_browser_write_is_quarantined(): assert disposition(CandidateRisk("x",browser_write=True))=="QUARANTINE_SANDBOX_ONLY"
def test_security_bypass_rejected(): assert disposition(CandidateRisk("x",security_bypass=True))=="REJECT_UNSAFE_CAPABILITY"
def test_no_external_candidate_runs_on_host(): assert not may_run_on_host(CandidateRisk("x"))
