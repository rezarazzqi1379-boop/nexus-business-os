import copy
import json
from pathlib import Path

from nexus_verticals.hydrotester_readiness import evaluate_matrix, highest_readiness_without_selection


MATRIX_PATH = Path("data/procurement/hydrotester_qualification_matrix_v0_2.json")


def load_matrix():
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def by_id(results):
    return {item.supplier_id: item for item in results}


def test_current_matrix_blocks_supplier_selection():
    matrix = load_matrix()
    results = evaluate_matrix(matrix)
    assert results
    assert all(result.selection_allowed is False for result in results)


def test_current_authority_is_rev1_2_and_supersedes_stale_dimensions():
    matrix = load_matrix()
    assert matrix["matrix_version"] == "0.2"
    assert matrix["authority_revision"] == "buyer_engineer_rev1.2"
    baseline = matrix["buyer_baseline"]
    assert baseline["wall_thickness_mm"] == {"min": 6, "max": 20, "status": "confirmed"}
    assert baseline["pipe_length_m"] == {"min": 9, "max": 12, "status": "confirmed"}
    assert baseline["required_throughput"]["value"] == 60


def test_superseded_supplier_dimensions_do_not_count_as_usable_readiness():
    matrix = load_matrix()
    results = by_id(evaluate_matrix(matrix))
    marley = next(item for item in matrix["candidates"] if item["supplier_id"] == "marley-wuxi")
    assert marley["fields"]["wall_thickness_range"]["status"] == "superseded_by_buyer_revision"
    assert marley["fields"]["length_range"]["status"] == "superseded_by_buyer_revision"
    assert results["marley-wuxi"].selection_allowed is False


def test_all_candidates_block_on_geometry_pressure_envelope():
    results = evaluate_matrix(load_matrix())
    assert all("pressure_envelope_vs_geometry" in item.blocking_fields for item in results)


def test_buyer_open_end_condition_prevents_selection():
    matrix = load_matrix()
    assert matrix["buyer_baseline"]["pipe_end_geometry_and_sealing_interface"]["blocking"] is True
    results = evaluate_matrix(matrix)
    assert all("buyer_baseline_has_unresolved_blockers" in item.rationale for item in results)


def test_marley_power_inconsistency_is_explicit_blocker():
    results = by_id(evaluate_matrix(load_matrix()))
    marley = results["marley-wuxi"]
    assert "power_and_utilities" in marley.inconsistent_fields
    assert "candidate_has_internal_document_inconsistencies" in marley.rationale


def test_yaxing_budgetary_throughput_is_not_selection_evidence():
    matrix = load_matrix()
    yaxing = next(item for item in matrix["candidates"] if item["supplier_id"] == "yaxing-dezhou")
    assert yaxing["fields"]["cycle_time_or_throughput"]["value"] == "1 pc/min"
    assert yaxing["fields"]["cycle_time_or_throughput"]["status"] == "supplier_stated_budgetary"
    result = by_id(evaluate_matrix(matrix))["yaxing-dezhou"]
    assert result.selection_allowed is False


def test_gh_price_is_non_final_and_does_not_create_technical_readiness():
    matrix = load_matrix()
    gh = next(item for item in matrix["candidates"] if item["supplier_id"] == "gh-petro")
    assert gh["fields"]["price"]["value"] == "USD 542800"
    assert gh["fields"]["price"]["status"] == "quoted_non_final_subject_to_final_specification"
    result = by_id(evaluate_matrix(matrix))["gh-petro"]
    assert result.selection_allowed is False


def test_unrecognized_status_fails_closed_even_when_buyer_blockers_are_cleared():
    matrix = copy.deepcopy(load_matrix())
    for value in matrix["buyer_baseline"].values():
        if isinstance(value, dict):
            value["blocking"] = False

    candidate = matrix["candidates"][0]
    for field in candidate["fields"].values():
        field["value"] = field.get("value") or "provided"
        field["status"] = "supplier_stated"
    candidate["fields"]["automation"]["status"] = "mystery_status"

    result = by_id(evaluate_matrix(matrix))[candidate["supplier_id"]]
    assert result.selection_allowed is False
    assert "candidate_has_unresolved_qualification_fields" in result.rationale


def test_missing_non_blocker_field_cannot_silently_allow_final_selection():
    matrix = copy.deepcopy(load_matrix())
    for value in matrix["buyer_baseline"].values():
        if isinstance(value, dict):
            value["blocking"] = False

    candidate = matrix["candidates"][0]
    for field in candidate["fields"].values():
        field["value"] = "provided"
        field["status"] = "supplier_stated"
    candidate["fields"]["warranty"] = {"value": None, "status": "pending"}

    result = by_id(evaluate_matrix(matrix))[candidate["supplier_id"]]
    assert result.selection_allowed is False
    assert "warranty" in result.missing_fields
    assert "candidate_has_unresolved_qualification_fields" in result.rationale


def test_no_supplier_is_shortlisted_before_rev1_2_reconfirmation():
    matrix = load_matrix()
    decision = matrix["current_decision"]
    assert decision["shortlist"] == []
    assert set(decision["conditional"]) == {"marley-wuxi", "yaxing-dezhou", "gh-petro"}
    assert decision["selected_supplier"] is None


def test_no_currency_conversion_or_price_ranking_is_performed():
    matrix = load_matrix()
    top = highest_readiness_without_selection(matrix)
    assert top.selection_allowed is False
