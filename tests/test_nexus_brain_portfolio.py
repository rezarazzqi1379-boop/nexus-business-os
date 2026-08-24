from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.projection import portfolio_projection, project_projection


def test_portfolio_contains_four_canonical_projects():
    graph = canonical_portfolio_graph()
    projection = portfolio_projection(graph)
    assert projection["project_count"] == 4
    assert {p["project_id"] for p in projection["projects"]} == {
        "PRJ-HYD-01",
        "PRJ-KCL-01",
        "PRJ-HTL-01",
        "PRJ-CAN-01",
    }


def test_every_tier_a_fact_has_retrievable_provenance():
    graph = canonical_portfolio_graph()
    for node in graph.nodes.values():
        if node.authority_tier.value == "canonical_authority" and node.epistemic_status.value == "fact":
            assert graph.trace_provenance(node.id)


def test_kcl_minimum_is_61_not_silently_rewritten_to_62():
    graph = canonical_portfolio_graph()
    p = project_projection(graph, "PRJ-KCL-01")
    k2o = next(item for item in p["requirements"] if item["id"] == "KCL-K2O")
    assert k2o["attributes"]["value"] == 61
    reference = next(item for item in p["facts"] if item["id"] == "KCL-REF-62")
    assert "62%" in reference["attributes"]["value"]


def test_kcl_dynamic_commercial_unknowns_block_consequential_use():
    graph = canonical_portfolio_graph()
    p = project_projection(graph, "PRJ-KCL-01")
    assert p["consequential_use_allowed"] is False
    assert "blocking_unknown" in p["blockers"]


def test_heat_treatment_revalidation_hold_is_visible_and_isolated_from_hydro():
    graph = canonical_portfolio_graph()
    htl = project_projection(graph, "PRJ-HTL-01")
    hyd = project_projection(graph, "PRJ-HYD-01")
    assert htl["consequential_use_allowed"] is False
    assert htl["counts"]["contradictions"] == 1
    assert any(item["id"] == "HTL-UNK-REVALIDATE" for item in htl["unknowns"])
    assert not any(item["id"].startswith("HYD-") for item in htl["requirements"])
    assert not any(item["id"].startswith("HTL-") for item in hyd["requirements"])


def test_can_forming_scopes_remain_separate_and_supplier_speed_is_claim_only():
    graph = canonical_portfolio_graph()
    p = project_projection(graph, "PRJ-CAN-01")
    req_ids = {item["id"] for item in p["requirements"]}
    assert {"CAN-SCOPE-A", "CAN-SCOPE-B"}.issubset(req_ids)
    claim_ids = {item["id"] for item in p["claims"]}
    assert {"CAN-GE-MAX", "CAN-GE-STABLE"}.issubset(claim_ids)
    assert p["consequential_use_allowed"] is False


def test_hydro_projection_preserves_current_canonical_dimensions():
    graph = canonical_portfolio_graph()
    p = project_projection(graph, "PRJ-HYD-01")
    values = {item["id"]: item["attributes"].get("value") for item in p["requirements"]}
    assert values["HYD-OD"] == "89-180"
    assert values["HYD-WT"] == "6-20"
    assert values["HYD-LEN"] == "9-12"
    assert values["HYD-PMAX"] == 120
    assert values["HYD-TPH"] == 60


def test_projection_is_json_serializable():
    import json

    graph = canonical_portfolio_graph()
    encoded = json.dumps(portfolio_projection(graph), sort_keys=True)
    assert "PRJ-HYD-01" in encoded
    assert "PRJ-KCL-01" in encoded
