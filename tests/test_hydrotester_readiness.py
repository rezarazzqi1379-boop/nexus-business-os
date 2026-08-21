import json
from pathlib import Path

from nexus_verticals.hydrotester_readiness import evaluate_matrix, highest_readiness_without_selection


MATRIX_PATH = Path("data/procurement/hydrotester_qualification_matrix_v0_1.json")


def load_matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def by_id(results):
    return {item.supplier_id: item for item in results}


def test_current_matrix_blocks_supplier_selection():
    matrix = load_matrix()
    results = evaluate_matrix(matrix)
    assert results
    assert all(result.selection_allowed is False for result in results)


def test_marley_has_highest_current_evidence_completeness_without_being_selected():
    matrix = load_matrix()
    top = highest_readiness_without_selection(matrix)
    assert top.supplier_id == "marley-wuxi"
    assert top.selection_allowed is False


def test_marley_power_inconsistency_is_explicit_blocker():
    results = by_id(evaluate_matrix(load_matrix()))
    marley = results["marley-wuxi"]
    assert "power_and_utilities" in marley.inconsistent_fields
    assert "candidate_has_internal_document_inconsistencies" in marley.rationale


def test_all_candidates_block_on_pressure_envelope():
    results = evaluate_matrix(load_matrix())
    assert all("pressure_envelope_vs_geometry" in item.blocking_fields for item in results)


def test_buyer_unknowns_prevent_selection_even_if_candidate_fields_are_filled():
    matrix = load_matrix()
    candidate = matrix["candidates"][0]
    for field in candidate["fields"].values():
        field["value"] = field.get("value") or "provided"
        field["status"] = "supplier_stated"
    result = by_id(evaluate_matrix(matrix))[candidate["supplier_id"]]
    assert result.selection_allowed is False
    assert "buyer_baseline_has_unresolved_blockers" in result.rationale


def test_no_currency_conversion_or_price_ranking_is_performed():
    matrix = load_matrix()
    results = by_id(evaluate_matrix(matrix))
    assert results["marley-wuxi"].readiness_percent > results["yaxing-dezhou"].readiness_percent
    assert results["marley-wuxi"].selection_allowed is False
    assert results["yaxing-dezhou"].selection_allowed is False
