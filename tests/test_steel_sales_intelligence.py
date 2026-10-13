from steel_sales_intelligence import evaluate_lead, provider_payload

def test_paid_enrichment_is_fail_closed_without_approval():
    gate=evaluate_lead(evidence_count=2,material_fit=True,named_company=True)
    assert gate.discovery_allowed is True
    assert gate.paid_enrichment_allowed is False
    assert "paid_enrichment_requires_exact_scope_approval" in gate.blockers

def test_compliance_market_blocks_outreach_until_cleared():
    gate=evaluate_lead(evidence_count=3,material_fit=True,named_company=True,
                       outreach_approved=True,compliance_required=True,compliance_cleared=False)
    assert gate.outreach_allowed is False
    assert "compliance_clearance_required" in gate.blockers

def test_provider_registry_keeps_external_repos_experimental():
    providers={x["provider_id"]:x for x in provider_payload()["providers"]}
    assert providers["external-sales-agent-repos"]["state"]=="EXPERIMENT_ONLY"
