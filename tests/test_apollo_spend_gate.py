from apollo_spend_gate import assess_spend
def test_high_fit_still_requires_free_resolution():
 d=assess_spend(buyer_fit=90,evidence_current=True,dedup_clear=True,free_resolution_attempted=False,existing_contact=False,expected_value=True)
 assert not d.eligible and "free_resolution_required_first" in d.blockers
def test_existing_contact_blocks_paid_enrichment():
 d=assess_spend(buyer_fit=90,evidence_current=True,dedup_clear=True,free_resolution_attempted=True,existing_contact=True,expected_value=True)
 assert not d.eligible
def test_paid_enrichment_can_become_eligible_but_not_authorized():
 d=assess_spend(buyer_fit=90,evidence_current=True,dedup_clear=True,free_resolution_attempted=True,existing_contact=False,expected_value=True)
 assert d.eligible and d.confidence==100
