from nexus_brain.fixtures import canonical_portfolio_graph
from nexus_brain.html import render_portfolio_html
from nexus_brain.projection import portfolio_projection


def test_html_surface_contains_all_projects_and_governance_state():
    html = render_portfolio_html(portfolio_projection(canonical_portfolio_graph()))
    for project_id in ("PRJ-HYD-01", "PRJ-KCL-01", "PRJ-HTL-01", "PRJ-CAN-01"):
        assert project_id in html
    assert "NEXUS BUSINESS OS · BRAIN · READ ONLY" in html
    assert "BLOCKED" in html
    assert "Contradiction radar" in html


def test_html_exposes_fact_claim_unknown_without_hiding_epistemic_state():
    html = render_portfolio_html(portfolio_projection(canonical_portfolio_graph()))
    assert ">FACT<" in html
    assert ">CLAIM<" in html
    assert ">UNKNOWN<" in html


def test_html_is_dependency_free_document():
    html = render_portfolio_html(portfolio_projection(canonical_portfolio_graph()))
    assert html.startswith("<!doctype html>")
    assert "<script" not in html.lower()
    assert "http://" not in html.lower()
    assert "https://" not in html.lower()
