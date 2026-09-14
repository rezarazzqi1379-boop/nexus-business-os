"""First executable Expert Foundry proof: evidence in, governed research state out."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from expert_foundry import ExpertFoundryStore, HypothesisRecord, KnowledgeRecord, ResearchTrace


REQUIRED_HEAT_SECTIONS = (
    "equipment", "chemistry", "charge_and_additions", "thermal_timeline",
    "casting", "quality_results", "maintenance_deviations", "operator_observations",
    "raw_evidence",
)


def assess_factory_input(payload: dict) -> list[str]:
    """Return precise gaps; truthy placeholders never establish readiness."""
    gaps: list[str] = []
    product = payload.get("product")
    if not isinstance(product, dict):
        gaps.append("product")
    else:
        for field in ("form", "grade", "acceptance_standard"):
            if not isinstance(product.get(field), str) or not product[field].strip():
                gaps.append(f"product.{field}")
    route = payload.get("production_route")
    if not isinstance(route, dict) or not route.get("route_id"):
        gaps.append("production_route.route_id")
    heats = payload.get("heats")
    if not isinstance(heats, list) or len(heats) != 2:
        return gaps + ["heats.requires_exactly_two_historical_records"]
    outcomes: set[str] = set()
    seen_ids: set[str] = set()
    for index, heat in enumerate(heats):
        prefix = f"heats[{index}]"
        if not isinstance(heat, dict):
            gaps.append(prefix)
            continue
        heat_id = heat.get("heat_id")
        if not isinstance(heat_id, str) or not heat_id.strip() or heat_id in seen_ids:
            gaps.append(f"{prefix}.heat_id_unique")
        else:
            seen_ids.add(heat_id)
        outcome = heat.get("outcome")
        if outcome not in {"ACCEPTABLE", "DEFECTIVE"}:
            gaps.append(f"{prefix}.outcome")
        else:
            outcomes.add(outcome)
        for section in REQUIRED_HEAT_SECTIONS:
            value = heat.get(section)
            if not isinstance(value, (dict, list)) or not value:
                gaps.append(f"{prefix}.{section}")
        timeline = heat.get("thermal_timeline")
        for measurement in timeline if isinstance(timeline, list) else []:
            if not isinstance(measurement, dict) or not all(measurement.get(key) not in (None, "") for key in
                ("value", "unit", "measured_at", "source_locator", "uncertainty")):
                gaps.append(f"{prefix}.thermal_timeline.measurement_contract")
                break
    if outcomes != {"ACCEPTABLE", "DEFECTIVE"}:
        gaps.append("heats.requires_one_acceptable_and_one_defective")
    return gaps

BASELINE_SOURCES = (
    {
        "record_id": "source_ingot_review_2024",
        "title": "Macrosegregation and shrinkage porosity in large steel ingots",
        "locator": "https://doi.org/10.1016/j.pnsc.2024.05.009",
        "statement": "Ingot quality depends on coupled composition, size, solidification conditions, flow, segregation and shrinkage mechanisms.",
    },
    {
        "record_id": "source_macrosegregation_2005",
        "title": "Macrosegregation in steel strands and ingots",
        "locator": "https://doi.org/10.1016/j.msea.2005.08.203",
        "statement": "Macrosegregation is difficult to remove downstream and requires process-specific characterization and modelling.",
    },
)


def run_proof(factory_input: dict, output_root: Path, now: str | None = None) -> dict:
    project_id = factory_input.get("project_id", "")
    if not project_id:
        raise ValueError("project_id_required")
    timestamp = now or datetime.now(timezone.utc).isoformat()
    store = ExpertFoundryStore(output_root)
    source_refs = []
    for source in BASELINE_SOURCES:
        record = KnowledgeRecord(
            record_id=source["record_id"], record_type="SOURCE", domain="steel_ingot",
            title=source["title"], statement=source["statement"],
            source_class="PRIMARY_RESEARCH", source_locator=source["locator"],
            captured_at=timestamp, confidence=0.0, project_id=project_id,
        )
        store.append(record)
        source_refs.append(record.record_id)

    missing = assess_factory_input(factory_input)
    trace = ResearchTrace(
        run_id="run_ingot_baseline_001", objective="Assess readiness for a safe steel-ingot research cycle",
        exact_queries=(), provider_ids=("repository_curated_baseline_v0_1",), source_refs=tuple(source_refs),
        rejected_source_refs=(),
        gap_refs=tuple(f"gap_{sha256(field.encode('utf-8')).hexdigest()[:16]}" for field in missing),
        started_at=timestamp, stopped_at=timestamp,
        stopping_reason="Baseline established; factory-specific inference blocked until measured inputs arrive.",
        project_id=project_id, retrieval_mode="STATIC_CURATED",
    )
    store.append(trace)

    hypothesis = HypothesisRecord(
        hypothesis_id="hypothesis_data_before_recipe_001", domain="steel_ingot",
        problem="A production recommendation cannot be bounded without plant measurements.",
        proposed_mechanism="Composition, thermal history, geometry and process practice interact during solidification.",
        predicted_outcome="Completing the input contract enables ranked, falsifiable defect hypotheses instead of generic advice.",
        falsification_test="Provide a complete historical heat record and verify whether the system can reproduce observed defect classes without using outcome leakage.",
        evidence_refs=tuple(source_refs), experience_refs=(),
        alternative_hypotheses=("Existing plant data may be insufficiently calibrated.", "The dominant defect may arise downstream of casting."),
        created_at=timestamp, project_id=project_id,
    )
    store.append(hypothesis)
    snapshot = store.create_snapshot("baseline_001")
    return {
        "proof_stage": "PHASE_0_PREFLIGHT",
        "status": "READY_FOR_FACTORY_DATA" if missing else "READY_FOR_RETROSPECTIVE_ANALYSIS",
        "project_id": project_id,
        "missing_fields": missing,
        "source_refs": source_refs,
        "hypothesis_id": hypothesis.hypothesis_id,
        "chain_valid": store.verify_chain(),
        "snapshot": str(snapshot),
        "prohibited": ["automatic recipe change", "equipment control", "unsupervised experiment"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run_proof(json.loads(args.input.read_text(encoding="utf-8")), args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
