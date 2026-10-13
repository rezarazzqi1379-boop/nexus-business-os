from candidate_registry import *

def test_candidate_requires_evidence_before_study():
 c=CandidateRecord("x","owner/repo",CandidateState.DISCOVERED)
 assert next_candidate_state(c) is CandidateState.DISCOVERED

def test_candidate_requires_acceptance_before_sandbox():
 c=CandidateRecord("x","owner/repo",CandidateState.STUDIED,evidence_refs=("ref",))
 assert next_candidate_state(c) is CandidateState.STUDIED

def test_failed_sandbox_rejects():
 c=CandidateRecord("x","owner/repo",CandidateState.SANDBOXED,evidence_refs=("ref",),acceptance_tests=("t",))
 assert next_candidate_state(c) is CandidateState.REJECTED

def test_ablation_win_admits_only_unprotected_runtime():
 c=CandidateRecord("x","owner/repo",CandidateState.ABLATED,ablation_win=True)
 assert next_candidate_state(c) is CandidateState.ADMITTED
 p=CandidateRecord("x","owner/repo",CandidateState.ABLATED,ablation_win=True,protected_runtime=True)
 assert next_candidate_state(p) is CandidateState.ABLATED
