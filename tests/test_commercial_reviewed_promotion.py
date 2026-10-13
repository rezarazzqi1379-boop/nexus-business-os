from commercial_chain_graph import candidate_edge, promote_reviewed

def _case():
    edge = candidate_edge(source_id="supplier-1", relation="SUPPLIED_TO", target_id="buyer-1",
                          evidence_refs=("source:a", "source:b"),
                          source_families=("official", "customs"))
    receipt = dict(decision="APPROVED", project_id="PRJ-TEST",
                   source_id="supplier-1", target_id="buyer-1", relation="SUPPLIED_TO",
                   evidence_digests=("sha256:a", "sha256:b"),
                   reviewer_id="reviewer-1", receipt_id="receipt-1")
    return edge, receipt

def test_exact_review_receipt_allows_structural_promotion():
    edge, receipt = _case()
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:b")).state == "VERIFIED"

def test_missing_review_fails_closed():
    edge, receipt = _case()
    assert promote_reviewed(edge, receipt={}, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:b")).state == "CANDIDATE"

def test_cross_project_receipt_fails_closed():
    edge, receipt = _case()
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-OTHER",
                            evidence_digests=("sha256:a", "sha256:b")).state == "CANDIDATE"

def test_tampered_evidence_digest_fails_closed():
    edge, receipt = _case()
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:tampered")).state == "CANDIDATE"

def test_wrong_relationship_endpoints_fail_closed():
    edge, receipt = _case()
    receipt["target_id"] = "buyer-2"
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:b")).state == "CANDIDATE"

def test_unreviewed_source_family_claim_is_insufficient():
    edge, receipt = _case()
    receipt["decision"] = "PENDING"
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:b")).state == "CANDIDATE"

def test_duplicate_evidence_digests_fail_closed():
    edge, receipt = _case()
    receipt["evidence_digests"] = ("sha256:a", "sha256:a")
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("sha256:a", "sha256:a")).state == "CANDIDATE"

def test_malformed_evidence_digests_fail_closed():
    edge, receipt = _case()
    receipt["evidence_digests"] = ("a", "b")
    assert promote_reviewed(edge, receipt=receipt, project_id="PRJ-TEST",
                            evidence_digests=("a", "b")).state == "CANDIDATE"
