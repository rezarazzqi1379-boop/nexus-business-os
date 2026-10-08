from external_capability_admission import *

def test_all_external_candidates_fail_closed_for_production():
 assert all(not may_run_in_production(c) for c in candidates())

def test_untrusted_or_model_capabilities_require_sandbox():
 assert all(requires_sandbox(c) for c in candidates() if c.untrusted_input or c.models)

def test_docling_and_paddle_are_sandboxed():
 by={c.repo:c for c in candidates()}
 assert by["docling-project/docling"].admission==Admission.SANDBOX
 assert by["PaddlePaddle/PaddleOCR"].admission==Admission.SANDBOX

def test_ocds_standard_is_mechanism_merge_not_runtime_authority():
 by={c.repo:c for c in candidates()}
 assert by["open-contracting/standard"].admission==Admission.MERGE_NATIVE
 assert not may_run_in_production(by["open-contracting/standard"])

def test_changedetection_full_install_is_deferred_due_overlap():
 by={c.repo:c for c in candidates()}
 assert by["dgtlmoon/changedetection.io"].admission==Admission.DEFER

def test_every_active_candidate_has_acceptance_test_and_rollback():
 for c in candidates():
  assert c.acceptance_test
  assert c.rollback

def test_install_order_starts_with_semantics_then_document_parser():
 assert install_order()[:2]==("open-contracting/standard","docling-project/docling")
