from nexus_core.agent_catalog import AgentCatalogEntry, active_catalog, candidates_for_problem, seed_catalog, should_revisit, validate_catalog


def test_seed_catalog_is_valid_and_persistent():
    entries = seed_catalog()
    assert not validate_catalog(entries)
    assert len(entries) >= 15
    assert any(e.lifecycle == "DEFERRED" for e in entries)
    assert any(e.lifecycle == "DISCOVERED" for e in entries)
    assert any(e.lifecycle == "EXPERIMENT" for e in entries)


def test_deferred_candidates_are_retained_for_future_revisit():
    entries = seed_catalog()
    temporal = next(e for e in entries if e.catalog_id == "AGT-TEMPORAL")
    assert temporal in active_catalog(entries)
    assert should_revisit(temporal, "repeated-state-loss") is True


def test_rejected_and_archived_are_not_active_or_revisited():
    base = seed_catalog()[0]
    rejected = AgentCatalogEntry(
        "AGT-REJECTED", "Rejected Tool", "OTHER", "https://example.com", "2026-08-28", "REJECTED",
        ("x",), ("y",), ("need-x",), "test", "rollback"
    )
    archived = AgentCatalogEntry(
        "AGT-ARCHIVED", "Archived Tool", "OTHER", "https://example.org", "2026-08-28", "ARCHIVED",
        ("x",), ("y",), ("need-x",), "test", "rollback"
    )
    active = active_catalog((base, rejected, archived))
    assert rejected not in active and archived not in active
    assert should_revisit(rejected, "need-x") is False


def test_problem_lookup_returns_future_and_current_options():
    results = candidates_for_problem(seed_catalog(), "coding-agent")
    ids = {e.catalog_id for e in results}
    assert "AGT-OPENCODE" in ids
    assert "AGT-OPEN-SWE" in ids
    assert "AGT-GOOSE" in ids
    assert "AGT-PLANDEX" in ids


def test_duplicate_identity_fails_closed():
    one = seed_catalog()[0]
    errors = validate_catalog((one, one))
    assert any("duplicate catalog_id" in e for e in errors)


def test_superseded_requires_existing_target():
    bad = AgentCatalogEntry(
        "AGT-OLD", "Old", "FRAMEWORK", "https://example.com/old", "2026-08-28", "SUPERSEDED",
        ("agent-runtime",), ("agents",), ("major-update",), "test", "rollback", superseded_by="AGT-MISSING"
    )
    errors = validate_catalog((bad,))
    assert any("superseded_by target missing" in e for e in errors)


def test_no_entry_self_authorizes_adoption_or_external_action():
    for entry in seed_catalog():
        assert entry.lifecycle != "ADOPTED_ADAPTER"
        assert entry.acceptance_test.strip()
        assert entry.rollback.strip()
