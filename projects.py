from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectPolicy:
    project_id: str
    status: str
    priority: int
    objective: str
    next_evidence: tuple[str, ...]
    forbidden_actions: tuple[str, ...] = ()


PROJECTS: dict[str, ProjectPolicy] = {
    "hydrostatic_tester": ProjectPolicy(
        "hydrostatic_tester", "active", 100, "Obtain a technically valid and priced 120 MPa proposal",
        ("steel_grade", "pressure_basis", "end_configuration", "pipes_per_hour", "fat_tpi"),
        ("outreach_boyu",),
    ),
    "kcl_mop": ProjectPolicy(
        "kcl_mop", "active", 90, "Qualify supply for white fine MOP used as SOP feed",
        ("official_import_rule", "coa_match", "price", "payment_route", "shipment_structure"),
    ),
    "can_forming": ProjectPolicy(
        "can_forming", "active", 85, "Obtain comparable necking-only and complete-line offers",
        ("necking_only_price", "stable_cpm_fat", "scope_matrix", "delivery", "warranty"),
    ),
    "heat_treatment": ProjectPolicy(
        "heat_treatment", "hold", 10, "Preserve evidence without further supplier activity",
        ("written_reactivation",), ("supplier_outreach", "commercial_commitment"),
    ),
    "food_additives": ProjectPolicy(
        "food_additives", "research", 45, "Validate demand and margin before supplier outreach",
        ("buyer_demand", "hs_code", "landed_cost", "regulatory_path"),
    ),
    "coffee_import": ProjectPolicy(
        "coffee_import", "research", 40, "Validate one-container green coffee opportunity",
        ("buyer_confirmation", "current_price", "landed_cost", "payment_route"),
    ),
    "tinplate_pi": ProjectPolicy(
        "tinplate_pi", "blocked", 35, "Complete a defensible proforma invoice",
        ("seller_identity", "item_b_quantity", "price", "incoterm", "payment_terms"),
    ),
    "portfolio_platform": ProjectPolicy(
        "portfolio_platform", "separate_workstream", 30, "Deliver a credible public portfolio product",
        ("repository_state", "deployment_owner", "acceptance_test"),
    ),
    "PRJ-FAL-01": ProjectPolicy(
        "PRJ-FAL-01", "research", 55,
        "Reconcile FAL-A/FAL-B structural models without promoting disputed commercial authority",
        ("dual_role_schema", "legacy_api_compatibility", "lane_isolation", "authority_reconciliation"),
        ("canonical_promotion", "cross_lane_evidence_transfer", "live_provider_activation"),
    ),
}


def get_project(project_id: str) -> ProjectPolicy:
    try:
        return PROJECTS[project_id]
    except KeyError as exc:
        raise ValueError("unknown_project") from exc

