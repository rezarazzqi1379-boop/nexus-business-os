from nexus_core.hydrotester_vertical import HydroRequirement, VendorEvidence, evaluate_live_hydrotester, po_ready


def test_latest_marley_reply_fails_throughput_gate():
    reqs = (
        HydroRequirement("HYD-TPH", "throughput_168_120_7s", "60 pipes/hour at agreed high-pressure duty points", "Hydrostatic_Tester_Engineering_Master_v1.1_2026-08-24"),
        HydroRequirement("HYD-STRUCT", "structural_calculations", "signed worst-case calculations/FEA incl safety factor", "Hydrostatic_Tester_Engineering_Master_v1.1_2026-08-24"),
        HydroRequirement("HYD-FAT", "fat_scope", "120 MPa + 10 consecutive + 1 h capacity + continuous operation with defined criteria", "Hydrostatic_Tester_Engineering_Master_v1.1_2026-08-24"),
    )
    src = "Gmail message 1a0474872759cd97 / Marley response 2026-08-28"
    evidence = (
        VendorEvidence("MAR-TPH", "throughput_168_120_7s", "15-20 pipes/hour implied by 3-4 minutes per pipe", src),
        VendorEvidence("MAR-STRUCT", "structural_calculations", "signed calculations promised later; 500 tonne basis described", src),
        VendorEvidence("MAR-FAT", "fat_scope", "120 MPa FAT + 10 consecutive + 1 h capacity + continuous operation", src),
    )
    findings = evaluate_live_hydrotester(reqs, evidence)
    by_id = {f.requirement_id: f for f in findings}
    assert by_id["HYD-TPH"].status == "DEVIATION"
    assert by_id["HYD-STRUCT"].status == "MISSING_EVIDENCE"
    assert by_id["HYD-FAT"].status in {"MATCH", "PARTIAL"}
    assert po_ready(findings) is False
