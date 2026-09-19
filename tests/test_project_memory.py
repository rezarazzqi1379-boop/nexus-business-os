from pathlib import Path

import pytest

from nexus_core.project_memory import MemoryEntry, ProjectMemoryStore


def make_store(tmp_path: Path) -> ProjectMemoryStore:
    return ProjectMemoryStore(tmp_path / "memory")


def test_record_and_query_round_trip(tmp_path):
    store = make_store(tmp_path)
    entry = store.record(
        "preference",
        "Reza wants a short sentence before starting any task, no acknowledgement recap.",
        decided_by="reza",
    )
    assert entry.entry_id == "preference-0001"
    results = store.query(namespace="preference")
    assert len(results) == 1
    assert results[0].statement == entry.statement


def test_persists_across_store_instances(tmp_path):
    store_a = make_store(tmp_path)
    store_a.record("decision", "Keep main's 220x220mm rolling-mill schema.", decided_by="reza")
    store_b = make_store(tmp_path)
    results = store_b.query(namespace="decision")
    assert len(results) == 1
    assert "220x220" in results[0].statement


def test_generated_entry_ids_increment_per_namespace(tmp_path):
    store = make_store(tmp_path)
    first = store.record("context", "Round-2 branch archaeology in progress.", decided_by="claude")
    second = store.record("context", "Round-2 branch archaeology complete.", decided_by="claude")
    assert first.entry_id == "context-0001"
    assert second.entry_id == "context-0002"


def test_duplicate_entry_id_rejected(tmp_path):
    store = make_store(tmp_path)
    store.record("decision", "First decision.", decided_by="reza", entry_id="decision-fixed")
    with pytest.raises(ValueError, match="duplicate_entry_id"):
        store.record("decision", "Second decision.", decided_by="reza", entry_id="decision-fixed")


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"statement": ""}, "invalid_statement"),
        ({"statement": "   "}, "invalid_statement"),
        ({"statement": "x" * 2001}, "statement_too_long"),
        ({"statement": "bad\x00byte"}, "invalid_control_characters_in_statement"),
        ({"decided_by": ""}, "invalid_decided_by"),
    ],
)
def test_validate_rejects_unsafe_entries(tmp_path, kwargs, expected):
    store = make_store(tmp_path)
    payload = {"statement": "A normal statement.", "decided_by": "reza"}
    payload.update(kwargs)
    with pytest.raises(ValueError, match=expected):
        store.record("preference", payload["statement"], decided_by=payload["decided_by"])


def test_invalid_namespace_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="invalid_namespace"):
        store.record("not_a_real_namespace", "x", decided_by="reza")  # type: ignore[arg-type]


def test_too_many_evidence_refs_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="too_many_evidence_refs"):
        store.record(
            "decision", "x", decided_by="reza",
            evidence_refs=tuple(f"ref-{i}" for i in range(21)),
        )


def test_query_filters_by_project_and_lane(tmp_path):
    store = make_store(tmp_path)
    store.record("context", "Hydrotester supplier registry updated.", decided_by="claude",
                 project_id="PRJ-HYD-01", lane="engineering")
    store.record("context", "FAL-B discovery run completed.", decided_by="claude",
                 project_id="PRJ-FAL-01", lane="research")
    hyd_only = store.query(project_id="PRJ-HYD-01")
    assert len(hyd_only) == 1
    assert "Hydrotester" in hyd_only[0].statement
    research_only = store.query(lane="research")
    assert len(research_only) == 1
    assert "FAL-B" in research_only[0].statement


def test_supersede_marks_outdated_without_deleting(tmp_path):
    store = make_store(tmp_path)
    old = store.record("decision", "Use feat's 150x150mm schema.", decided_by="claude-draft")
    new = store.record("decision", "Keep main's 220x220mm schema per Reza.", decided_by="reza")
    store.supersede("decision", old.entry_id, superseded_by=new.entry_id)
    all_entries = store.query(namespace="decision")
    assert len(all_entries) == 2
    current_only = store.query(namespace="decision", include_superseded=False)
    assert len(current_only) == 1
    assert current_only[0].entry_id == new.entry_id


def test_supersede_unknown_entry_id_rejected(tmp_path):
    store = make_store(tmp_path)
    real = store.record("decision", "Real decision.", decided_by="reza")
    with pytest.raises(KeyError, match="unknown_entry_id"):
        store.supersede("decision", "does-not-exist", superseded_by=real.entry_id)


def test_bootstrap_context_empty_store(tmp_path):
    store = make_store(tmp_path)
    assert store.bootstrap_context() == "(no recorded project memory yet)"


def test_bootstrap_context_excludes_superseded_and_includes_evidence(tmp_path):
    store = make_store(tmp_path)
    old = store.record("decision", "Old call.", decided_by="claude-draft")
    new = store.record(
        "decision", "Final call per Reza.", decided_by="reza",
        evidence_refs=(".nexus/state/CURRENT_STATE.md",),
    )
    store.supersede("decision", old.entry_id, superseded_by=new.entry_id)
    digest = store.bootstrap_context()
    assert "Old call." not in digest
    assert "Final call per Reza." in digest
    assert "CURRENT_STATE.md" in digest


def test_bootstrap_context_respects_limit(tmp_path):
    store = make_store(tmp_path)
    for i in range(5):
        store.record("context", f"Status update {i}.", decided_by="claude")
    digest = store.bootstrap_context(limit=2)
    assert "Status update 3." in digest
    assert "Status update 4." in digest
    assert "Status update 0." not in digest


def test_bootstrap_context_invalid_limit_rejected(tmp_path):
    store = make_store(tmp_path)
    with pytest.raises(ValueError, match="invalid_limit"):
        store.bootstrap_context(limit=0)


def test_memory_entry_from_json_round_trip():
    entry = MemoryEntry(
        entry_id="preference-0001",
        namespace="preference",
        statement="Prefers direct execution over lengthy explanation.",
        decided_by="reza",
        created_at="2026-09-19T00:00:00+00:00",
        project_id=None,
        lane=None,
        evidence_refs=(),
    )
    restored = MemoryEntry.from_json(entry.to_json())
    assert restored == entry
