from contract_code_audit import CapabilityEvidence,audit,classify

def test_documentation_never_implies_implementation():
 assert classify(CapabilityEvidence("x"))=="DESIGNED_ONLY"

def test_green_test_requires_implementation_evidence():
 assert classify(CapabilityEvidence("x",test_refs=("ci:1",)))=="DRIFTED"

def test_integration_requires_test_evidence():
 assert classify(CapabilityEvidence("x",implementation_refs=("code:x",),integration_refs=("graph:x",)))=="DRIFTED"

def test_evidenced_maturity_progression():
 assert classify(CapabilityEvidence("x",implementation_refs=("code:x",)))=="IMPLEMENTED"
 assert classify(CapabilityEvidence("x",implementation_refs=("code:x",),test_refs=("ci:1",)))=="TESTED"
 assert classify(CapabilityEvidence("x",implementation_refs=("code:x",),test_refs=("ci:1",),benchmark_refs=("bench:1",)))=="BENCHMARKED"

def test_supersession_is_explicit():
 assert classify(CapabilityEvidence("old",superseded_by="new"))=="SUPERSEDED"

def test_audit_exposes_prompt_only_gap():
 r=audit((CapabilityEvidence("prompt-only"),CapabilityEvidence("built",implementation_refs=("code:1",))))
 assert r["gaps"]==("prompt-only",)
