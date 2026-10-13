from external_capability_lab import *

def pattern(**kw):
 base=dict(pattern_id="browser_snapshot_extract",evidence_refs=("github:source","github:failure-history"),acceptance_tests=("extract_fixture",),deterministic=True,external_runtime_required=False)
 base.update(kw); return ExternalPattern(**base)

def test_no_measured_bottleneck_means_study_not_architecture_growth():
 assert lab_decision(pattern(),measured_bottleneck=False) is LabDecision.STUDY

def test_external_runtime_or_secret_stays_sandboxed():
 assert lab_decision(pattern(external_runtime_required=True),measured_bottleneck=True) is LabDecision.SANDBOX
 assert lab_decision(pattern(secrets_required=True),measured_bottleneck=True) is LabDecision.SANDBOX

def test_ablation_win_required_before_pattern_promotion():
 assert lab_decision(pattern(),measured_bottleneck=True,sandbox_passed=True) is LabDecision.ABLATE
 assert lab_decision(pattern(),measured_bottleneck=True,sandbox_passed=True,ablation_win=True) is LabDecision.PROMOTE_PATTERN

def test_extraction_requires_provenance_and_selector_validation():
 bad=ExtractionProof("snap","selector","",20,"source")
 assert not extraction_evidence_ready(bad)
 good=ExtractionProof("snap","selector","validated:20",20,"https://example.test")
 assert extraction_evidence_ready(good)

def test_eval_pattern_requires_trajectory_tool_failure_and_fault_checks():
 assert not evaluation_pattern_ready(EvaluationProof(True,True,True,False))
 assert evaluation_pattern_ready(EvaluationProof(True,True,True,True))
