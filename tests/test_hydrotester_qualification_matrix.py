import json
from pathlib import Path


MATRIX_PATH = Path("data/procurement/hydrotester_qualification_matrix_v0_1.json")
REGISTRY_PATH = Path("data/procurement/hydrotester_registry_v0_1.json")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_matrix_parses_and_tracks_current_buyer_blockers():
    data = load(MATRIX_PATH)
    assert data["matrix_version"] == "0.2"
    baseline = data["buyer_baseline"]
    assert baseline["required_test_pressure_envelope"]["blocking"] is True
    assert baseline["required_throughput_pipes_per_hour"]["value"] == 60
    assert baseline["required_throughput_pipes_per_hour"]["qualifier"] == "approximately"
    assert baseline["required_throughput_pipes_per_hour"]["blocking"] is False
    assert baseline["maximum_machine_design_rating_mpa"]["value"] == 120
    assert "relevant_duty_points" in baseline["maximum_machine_design_rating_mpa"]["status"]
    assert "varies by pipe size/configuration" in baseline["pressure_logic"]["value"]


def test_all_matrix_candidates_exist_in_supplier_registry():
    matrix = load(MATRIX_PATH)
    registry = load(REGISTRY_PATH)
    supplier_ids = {item["supplier_id"] for item in registry["suppliers"]}
    assert {item["supplier_id"] for item in matrix["candidates"]} <= supplier_ids


def test_no_candidate_is_marked_as_fully_120_mpa_verified():
    data = load(MATRIX_PATH)
    forbidden = {"verified", "fat_verified", "120_mpa_verified", "fully_qualified"}
    for candidate in data["candidates"]:
        assert candidate["qualification_state"] not in forbidden
        pressure_status = candidate["fields"]["pressure_capability"]["status"]
        assert pressure_status not in forbidden


def test_missing_geometry_pressure_envelope_blocks_every_candidate():
    data = load(MATRIX_PATH)
    for candidate in data["candidates"]:
        field = candidate["fields"]["pressure_envelope_vs_geometry"]
        assert field["status"] == "missing_blocker"


def test_suppliertr_is_unresolved_and_not_counted_as_supplier():
    registry = load(REGISTRY_PATH)
    supplier_ids = {item["supplier_id"] for item in registry["suppliers"]}
    unresolved = {item["channel_id"]: item for item in registry["unresolved_channels"]}
    assert "suppliertr-yakup" in unresolved
    assert unresolved["suppliertr-yakup"]["underlying_supplier_id"] is None
    assert "suppliertr-yakup" not in supplier_ids


def test_intermediary_routes_have_identity_gate_actions():
    data = load(MATRIX_PATH)
    for route in data["intermediary_routes"]:
        assert "identity_gate" in route["status"]
        assert route["evidence_ref"]
        assert route["action"]


def test_current_decision_does_not_select_supplier_prematurely():
    data = load(MATRIX_PATH)
    decision = data["current_decision"]
    assert decision["selected_supplier"] is None
    assert set(decision["shortlist"]) == {"marley-wuxi", "yaxing-dezhou", "gh-petro"}


def test_marley_power_inconsistency_is_not_silently_resolved():
    data = load(MATRIX_PATH)
    marley = next(item for item in data["candidates"] if item["supplier_id"] == "marley-wuxi")
    power = marley["fields"]["power_and_utilities"]
    assert "260 kVA" in power["value"]
    assert "30 kW" in power["value"]
    assert power["status"] == "internal_document_inconsistency_requires_clarification"


def test_yaxing_one_pipe_per_minute_is_not_treated_as_high_pressure_verified():
    data = load(MATRIX_PATH)
    yaxing = next(item for item in data["candidates"] if item["supplier_id"] == "yaxing-dezhou")
    throughput = yaxing["fields"]["cycle_time_or_throughput"]
    assert throughput["value"] == "1 pc/min"
    assert throughput["status"] == "supplier_stated_budgetary_matches_approximate_buyer_rate_not_high_pressure_verified"


def test_gh_quote_is_commercial_evidence_not_technical_qualification():
    data = load(MATRIX_PATH)
    gh = next(item for item in data["candidates"] if item["supplier_id"] == "gh-petro")
    assert gh["fields"]["od_range"]["value"] == "89-180 mm"
    assert gh["fields"]["pressure_capability"]["value"] == "maximum 120 MPa"
    assert gh["fields"]["price"]["value"] == "USD 542800"
    assert gh["fields"]["incoterm"]["value"] == "FOB Dalian"
    assert gh["fields"]["lead_time"]["value"] == "120 days"
    assert gh["qualification_state"] == "commercial_quote_received_technical_validation_required"
    assert gh["fields"]["pressure_envelope_vs_geometry"]["status"] == "missing_blocker"


def test_boyu_is_parked_and_cannot_be_silently_reactivated():
    data = load(MATRIX_PATH)
    parked = {item["supplier_id"]: item for item in data["excluded_or_parked"]}
    assert parked["boyu-petro"]["status"] == "parked_no_further_action"
    assert parked["boyu-petro"]["reactivation_rule"] == "only on explicit buyer instruction"
    assert "boyu-petro" not in data["current_decision"]["shortlist"]
