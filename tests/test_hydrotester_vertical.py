from nexus_core.hydrotester_vertical import HydroRequirement, VendorEvidence, evaluate_live_hydrotester, po_ready


def _requirements():
    src = "Hydrostatic_Tester_Engineering_Master_v1.1_2026-08-24"
    return (
        HydroRequirement("HYD-P", "pressure_capability", "120 MPa duty-dependent", src),
        HydroRequirement("HYD-TPH", "throughput_168_120_7s", "60 pipes/hour at OD 168.3 mm, 120 MPa, 7 s hold", src),
        HydroRequirement("HYD-ACC", "pressure_acceptance_rule", "one contractual calibrated pass/fail criterion", src),
        HydroRequirement("HYD-MATRIX", "capability_matrix_completeness", "OD x WT/ID x length x grade x end condition x pressure x hold x throughput", src),
        HydroRequirement("HYD-STRUCT", "structural_calculations", "signed worst-case calculations/FEA incl safety factor", src),
        HydroRequirement("HYD-TOOL", "tooling_scope", "complete tooling for contractual sizes", src),
        HydroRequirement("HYD-FAT", "fat_scope", "120 MPa + 10 consecutive + 1 h capacity + continuous operation with defined criteria", src),
        HydroRequirement("HYD-SCOPE", "final_scope_price", "complete agreed scope at reconciled commercial basis", src),
    )


def _gh_20260828():
    src = "Gmail message 1a048bfc44a30ac6 / signed 2026-08-28 attachment"
    return (
        VendorEvidence("GH-20260828-P", "pressure_capability", "120 MPa at signed duty points", src),
        VendorEvidence("GH-20260828-TPH", "throughput_168_120_7s", "60 pipes/hour at OD 168.3 mm, 120 MPa, 7 s hold", src),
        VendorEvidence("GH-20260828-ACC", "pressure_acceptance_rule", "pressure sensing accuracy ±0.25%; gauge class 1.6", src),
        VendorEvidence("GH-20260828-MATRIX", "capability_matrix_completeness", "OD,WT/ID,length,pressure,hold,throughput", src),
        VendorEvidence("GH-20260828-STRUCT", "structural_calculations", "310 metric ton axial-force summary; certificate after contract", src),
        VendorEvidence("GH-20260828-TOOL", "tooling_scope", "three included mould sizes; extra sizes USD 12,000 per pair/set", src),
        VendorEvidence("GH-20260828-FAT", "fat_scope", "confirmed without detailed pass/fail dossier", src),
        VendorEvidence("GH-20260828-SCOPE", "final_scope_price", "unchanged-price confirmation with tooling extras elsewhere", src),
    )


def test_latest_gh_signed_reply_is_not_po_ready():
    findings = evaluate_live_hydrotester(_requirements(), _gh_20260828())
    assert po_ready(findings) is False
    status = {f.requirement_id: f.status for f in findings}
    assert status["HYD-P"] == "MATCH"
    assert status["HYD-TPH"] == "MATCH"
    assert status["HYD-ACC"] == "MISSING_EVIDENCE"
    assert status["HYD-MATRIX"] == "MISSING_EVIDENCE"
    assert status["HYD-STRUCT"] == "MISSING_EVIDENCE"
    assert status["HYD-TOOL"] == "DEVIATION"
    assert status["HYD-FAT"] == "PARTIAL"
    assert status["HYD-SCOPE"] == "PARTIAL"


def test_conflicting_vendor_values_fail_closed():
    req = (HydroRequirement("HYD-P", "pressure_capability", "120 MPa duty-dependent", "master"),)
    evidence = (
        VendorEvidence("A", "pressure_capability", "120 MPa at signed duty points", "source-a"),
        VendorEvidence("B", "pressure_capability", "70 MPa only", "source-b"),
    )
    result = evaluate_live_hydrotester(req, evidence)
    assert result[0].status == "CONFLICT"
    assert po_ready(result) is False
