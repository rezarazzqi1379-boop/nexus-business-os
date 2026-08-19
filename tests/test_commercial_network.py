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
    assert qualify_commercial_network((candidate(),))[0].state == "qualified"


def test_contact_without_need_signal_is_not_qualified():
    assert qualify_commercial_network((candidate(need_signals=()),))[0].state != "qualified"


def test_unverified_name_does_not_become_opportunity():
    assert qualify_commercial_network((candidate(evidence_strength="unverified"),))[0].state != "qualified"


def test_weak_evidence_never_qualifies_even_with_complete_shape():
    assert qualify_commercial_network((candidate(evidence_strength="weak"),))[0].state == "research_more"


def test_duplicate_is_rejected():
    result = qualify_commercial_network((candidate(duplicate_of="existing:1"),))[0]
    assert result.state == "reject" and "duplicate_candidate" in result.reasons


def test_missing_evidence_is_rejected():
    result = qualify_commercial_network((candidate(evidence_refs=()),))[0]
    assert result.state == "reject" and "missing_evidence_refs" in result.reasons


def test_runtime_invalid_enum_is_rejected_fail_closed():
    result = qualify_commercial_network((candidate(evidence_strength="invented"),))[0]
    assert result.state == "reject" and "invalid_evidence_strength" in result.reasons


def test_duplicate_candidate_id_is_rejected():
    results = qualify_commercial_network((candidate(), candidate(company_name="Other Co")))
    assert any(item.state == "reject" and "duplicate_candidate_id" in item.reasons for item in results)


def test_duplicate_evidence_refs_are_rejected():
    result = qualify_commercial_network((candidate(evidence_refs=("source:1", "source:1")),))[0]
    assert result.state == "reject" and "invalid_evidence_refs" in result.reasons
