from evidence_hardening import (
    ClaimEvidence, ClaimRelation, ClaimState, EvidenceEnvelope, FreshnessClass,
    canonical_origin, claim_state, content_digest, independent_lineage_roots, stale,
)


def ev(eid="e1", project="P1", source="https://www.example.com/a", **kw):
    return EvidenceEnvelope(
        evidence_id=eid, project_id=project, source_locator=source,
        observed_at="2026-10-01T00:00:00Z", payload=kw.pop("payload", {"x": 1}), **kw
    )


def test_content_digest_is_order_independent_and_mutation_sensitive():
    assert content_digest({"a": 1, "b": 2}) == content_digest({"b": 2, "a": 1})
    assert content_digest({"a": 1}) != content_digest({"a": 2})


def test_canonical_origin_collapses_url_copies():
    assert canonical_origin(ev(source="https://www.EXAMPLE.com/a")) == "example.com"
    assert canonical_origin(ev(source="https://example.com/b")) == "example.com"


def test_independence_comes_from_lineage_roots_not_result_count():
    a = ev("a", lineage_roots=("official.example",))
    b = ev("b", source="https://mirror.invalid/copy", lineage_roots=("official.example",))
    c = ev("c", source="https://other.example/x", lineage_roots=("other.example",))
    assert independent_lineage_roots((a, b, c), "P1") == ("official.example", "other.example")


def test_project_isolation_for_independent_roots():
    assert independent_lineage_roots((ev("a"), ev("b", project="P2")), "P1") == ("example.com",)


def test_dynamic_without_refresh_deadline_is_stale_but_static_is_not():
    assert stale(ev(), "2026-10-02T00:00:00Z")
    assert not stale(ev(freshness_class=FreshnessClass.STATIC), "2030-01-01T00:00:00Z")


def test_refresh_deadline_controls_dynamic_freshness():
    x = ev(refresh_after="2026-10-03T00:00:00Z")
    assert not stale(x, "2026-10-02T00:00:00Z")
    assert stale(x, "2026-10-04T00:00:00Z")


def test_claim_conflict_fails_to_review_not_supported():
    a = ev("a", freshness_class=FreshnessClass.STATIC)
    b = ev("b", source="https://other.example/x", freshness_class=FreshnessClass.STATIC)
    links = (
        ClaimEvidence("c1", "a", "P1", ClaimRelation.SUPPORTS),
        ClaimEvidence("c1", "b", "P1", ClaimRelation.REFUTES),
    )
    assert claim_state("c1", links, (a, b), "P1", "2026-10-07T00:00:00Z") == ClaimState.NEEDS_REVIEW


def test_stale_support_cannot_remain_supported():
    a = ev("a", refresh_after="2026-10-02T00:00:00Z")
    links = (ClaimEvidence("c1", "a", "P1", ClaimRelation.SUPPORTS),)
    assert claim_state("c1", links, (a,), "P1", "2026-10-07T00:00:00Z") == ClaimState.STALE


def test_cross_project_evidence_cannot_support_claim():
    a = ev("a", project="P2", freshness_class=FreshnessClass.STATIC)
    links = (ClaimEvidence("c1", "a", "P1", ClaimRelation.SUPPORTS),)
    assert claim_state("c1", links, (a,), "P1", "2026-10-07T00:00:00Z") == ClaimState.UNRESOLVED
