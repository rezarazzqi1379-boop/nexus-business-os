from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Status = Literal["MATCH", "PARTIAL", "DEVIATION", "MISSING_EVIDENCE", "CONFLICT"]


@dataclass(frozen=True)
class HydroRequirement:
    requirement_id: str
    parameter: str
    canonical_value: str
    source_ref: str


@dataclass(frozen=True)
class VendorEvidence:
    evidence_id: str
    parameter: str
    value: str
    source_ref: str
    evidence_class: Literal["FACT", "MEASUREMENT", "CLAIM", "UNKNOWN"] = "CLAIM"


@dataclass(frozen=True)
class HydroFinding:
    requirement_id: str
    status: Status
    canonical_value: str
    vendor_value: str | None
    reason: str
    source_refs: tuple[str, ...]


def evaluate_live_hydrotester(
    requirements: Sequence[HydroRequirement],
    evidence: Sequence[VendorEvidence],
) -> tuple[HydroFinding, ...]:
    by_parameter: dict[str, list[VendorEvidence]] = {}
    for item in evidence:
        by_parameter.setdefault(item.parameter, []).append(item)

    findings: list[HydroFinding] = []
    for req in requirements:
        matches = by_parameter.get(req.parameter, [])
        if not matches:
            findings.append(HydroFinding(req.requirement_id, "MISSING_EVIDENCE", req.canonical_value, None,
                "No current vendor evidence supplied for this canonical requirement.", (req.source_ref,)))
            continue

        values = {m.value for m in matches}
        if len(values) > 1:
            findings.append(HydroFinding(req.requirement_id, "CONFLICT", req.canonical_value, " | ".join(sorted(values)),
                "Multiple current vendor values exist for the same parameter; do not average or guess.",
                (req.source_ref, *(m.source_ref for m in matches))))
            continue

        item = matches[0]
        value = item.value
        status: Status = "PARTIAL"
        reason = "Vendor evidence addresses the parameter but does not itself become canonical authority."

        if req.parameter == "pressure_capability":
            status = "MATCH" if value == "120 MPa at signed duty points" else "PARTIAL"
            reason = "Signed 120 MPa duty-point confirmation present." if status == "MATCH" else "Pressure statement does not fully bind the required duty points."
        elif req.parameter == "throughput_168_120_7s":
            status = "MATCH" if value == "60 pipes/hour at OD 168.3 mm, 120 MPa, 7 s hold" else "DEVIATION"
            reason = "Vendor signed the buyer throughput target at the stated high-pressure reference point." if status == "MATCH" else "Vendor throughput does not match the reference high-pressure duty point."
        elif req.parameter == "pressure_acceptance_rule":
            status = "MISSING_EVIDENCE"
            reason = "Sensor/gauge accuracy is not the same as one unambiguous contractual pressure pass/fail criterion."
        elif req.parameter == "capability_matrix_completeness":
            required_tokens = {"OD", "WT/ID", "length", "grade", "end condition", "pressure", "hold", "throughput"}
            present = {t.strip() for t in value.split(",") if t.strip()}
            missing = sorted(required_tokens - present)
            status = "MATCH" if not missing else "MISSING_EVIDENCE"
            reason = "Signed capability matrix contains every required dimension/duty field." if not missing else f"Capability matrix is incomplete; missing: {', '.join(missing)}."
        elif req.parameter == "structural_calculations":
            status = "MATCH" if value == "signed calculations/FEA with worst-case axial load and safety factor" else "MISSING_EVIDENCE"
            reason = "Required signed structural package supplied." if status == "MATCH" else "Axial-force summary/certificate promise is not the requested signed calculations/FEA and safety-factor basis."
        elif req.parameter == "tooling_scope":
            status = "DEVIATION" if "three included" in value and "extra" in value else "PARTIAL"
            reason = "Only three mould sizes are included; additional contractual sizes carry extra cost, so full tooling is not included at unchanged price." if status == "DEVIATION" else reason
        elif req.parameter == "fat_scope":
            status = "PARTIAL" if value == "confirmed without detailed pass/fail dossier" else "MATCH"
            reason = "FAT items were acknowledged, but detailed measurement methods, calibrated references and pass/fail dossier remain to be contractually closed." if status == "PARTIAL" else reason
        elif req.parameter == "final_scope_price":
            status = "PARTIAL"
            reason = "Unchanged-price confirmation exists, but tooling extras and the complete contractual inclusion/exclusion schedule must be reconciled before PO readiness."

        findings.append(HydroFinding(req.requirement_id, status, req.canonical_value, value, reason,
            (req.source_ref, item.source_ref)))

    return tuple(findings)


def po_ready(findings: Sequence[HydroFinding]) -> bool:
    return bool(findings) and all(f.status == "MATCH" for f in findings)
