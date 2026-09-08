"""First executable Expert Foundry proof: evidence in, governed research state out."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from expert_foundry import ExpertFoundryStore, HypothesisRecord, KnowledgeRecord, ResearchTrace


REQUIRED_FACTORY_FIELDS = (
    "product_grade", "target_chemistry", "furnace_type", "furnace_capacity",
    "charge_materials", "deoxidation_practice", "casting_method", "mould_geometry",
    "temperature_measurements", "sampling_plan", "observed_defects", "quality_tests",
)

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
            captured_at=timestamp, confidence=0.85, project_id=project_id,
        )
        store.append(record)
        source_refs.append(record.record_id)

    missing = [field for field in REQUIRED_FACTORY_FIELDS if not factory_input.get(field)]
    trace = ResearchTrace(
        run_id="run_ingot_baseline_001", objective="Assess readiness for a safe steel-ingot research cycle",
        exact_queries=(
            "steel ingot macrosegregation shrinkage porosity review",
            "steel ingot solidification process measurement quality",
        ),
        provider_ids=("public_web_search",), source_refs=tuple(source_refs),
        rejected_source_refs=(), gap_refs=tuple(f"gap_{field}" for field in missing),
        started_at=timestamp, stopped_at=timestamp,
        stopping_reason="Baseline established; factory-specific inference blocked until measured inputs arrive.",
        project_id=project_id,
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
        "status": "READY_FOR_FACTORY_DATA" if missing else "READY_FOR_BOUNDED_ANALYSIS",
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
