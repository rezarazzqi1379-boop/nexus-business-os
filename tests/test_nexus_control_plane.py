import pytest
from nexus_control_plane import *

def cap(name,functions,**kw):
    return CapabilityCandidate(name,frozenset(functions),("evidence:fixture",),("test:acceptance",),**kw)

def test_duplicate_capability_merges():
    d=evaluate_capability_admission(cap("new",{"search","fetch"},sandboxed=True),(cap("native",{"search","fetch"}),))
    assert d.action is Admission.MERGE

def test_write_or_secret_requires_exact_approval():
    d=evaluate_capability_admission(cap("crm",{"write"},sandboxed=True,external_write=True),())
    assert d.action is Admission.SANDBOX and d.requires_exact_approval

def test_untested_or_unevidenced_fails_closed():
    with pytest.raises(ValueError,match="evidence"): CapabilityCandidate("x",frozenset({"read"}),(),("t",)).validate()
    with pytest.raises(ValueError,match="acceptance"): CapabilityCandidate("x",frozenset({"read"}),("e",),()).validate()

def test_new_read_capability_stays_sandboxed_until_evaluated():
    assert evaluate_capability_admission(cap("reader",{"read"}),()).action is Admission.SANDBOX
    assert evaluate_capability_admission(cap("reader",{"read"},sandboxed=True),()).action is Admission.KEEP

def mature(**kw):
    base=dict(company_identity=True,product_application=True,buyer_role=True,procurement_signal=True,decision_maker=True,verified_contact=True,independent_sources=2,canonical_conversion_ready=True,canonical_sales_readiness="READY",canonical_stock_ready=True)
    base.update(kw); return ConversionProjection(**base)

def test_discovery_volume_is_not_conversion():
    e=ConversionProjection(company_identity=True,product_application=True,independent_sources=20)
    assert commercial_conversion_stage(e) is ConversionStage.EVIDENCED

def test_existing_conversion_gate_cannot_be_bypassed():
    assert commercial_conversion_stage(mature(canonical_conversion_ready=False)) is ConversionStage.BUYER_VERIFIED

def test_contact_cannot_bypass_unknown_compliance_or_readiness():
    assert commercial_conversion_stage(mature(canonical_sales_readiness="UNKNOWN")) is ConversionStage.CONTACT_VERIFIED
    assert commercial_conversion_stage(mature(canonical_sales_readiness="BLOCKED")) is ConversionStage.CONTACT_VERIFIED

def test_stock_currentness_binding_is_required_for_outreach_ready():
    assert commercial_conversion_stage(mature(canonical_stock_ready=False)) is ConversionStage.CONTACT_VERIFIED

def test_unresolved_contradiction_fails_closed():
    assert commercial_conversion_stage(mature(unresolved_contradiction=True)) is ConversionStage.DISCOVERED

def test_all_canonical_gates_required_for_outreach_ready():
    assert commercial_conversion_stage(mature()) is ConversionStage.OUTREACH_READY
