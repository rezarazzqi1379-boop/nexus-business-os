from nexus_core.commercial_network import CommercialCandidate, qualify_commercial_network


def candidate(**overrides):
    base = dict(
        candidate_id="c1", company_name="Pipe Co", market="Turkey",
        product_fit=("hydrotester",), need_signals=("pipe manufacturing",),
        role_signals=("procurement",), contact_paths=("official contact",),
        evidence_refs=("source:1",), evidence_strength="partial", path_type="direct",
    )
    base.update(overrides)
    return CommercialCandidate(**base)


def test_complete_evidence_backed_path_qualifies():
    result = qualify_commercial_network((candidate(),))
    assert result[0].state == "qualified"


def test_contact_without_need_signal_is_not_qualified():
    result = qualify_commercial_network((candidate(need_signals=()),))
    assert result[0].state != "qualified"


def test_unverified_name_does_not_become_opportunity():
    result = qualify_commercial_network((candidate(evidence_strength="unverified"),))
    assert result[0].state != "qualified"


def test_duplicate_is_rejected():
    result = qualify_commercial_network((candidate(duplicate_of="existing:1"),))
    assert result[0].state == "reject"
    assert "duplicate_candidate" in result[0].reasons


def test_missing_evidence_is_rejected():
    result = qualify_commercial_network((candidate(evidence_refs=()),))
    assert result[0].state == "reject"
