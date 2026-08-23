from nexus_control_plane.memory_lifecycle import (
    MemoryRecord,
    MemoryStatus,
    MemoryUse,
    evaluate_memory_for_use,
)


def rec(status=MemoryStatus.ACTIVE, **kw):
    base = dict(
        memory_id="m1",
        project_id="PRJ-HYD-01",
        source_ref="src:1",
        status=status,
        valid_from="2026-08-24",
    )
    base.update(kw)
    return MemoryRecord(**base)


def test_active_memory_can_enter_same_project_decision_context():
    out = evaluate_memory_for_use(rec(), project_id="PRJ-HYD-01", use=MemoryUse.DECISION_CONTEXT)
    assert out.include is True


def test_superseded_memory_is_excluded_from_current_decision_context():
    out = evaluate_memory_for_use(
        rec(MemoryStatus.SUPERSEDED, superseded_by="m2"),
        project_id="PRJ-HYD-01",
        use=MemoryUse.DECISION_CONTEXT,
    )
    assert out.include is False


def test_invalidated_memory_is_excluded_from_current_decision_context():
    out = evaluate_memory_for_use(rec(MemoryStatus.INVALIDATED), project_id="PRJ-HYD-01", use=MemoryUse.DECISION_CONTEXT)
    assert out.include is False


def test_cross_project_memory_is_never_silently_reused():
    out = evaluate_memory_for_use(rec(), project_id="PRJ-HTL-01", use=MemoryUse.DECISION_CONTEXT)
    assert out.include is False


def test_time_bounded_memory_requires_live_refresh_before_decision_use():
    out = evaluate_memory_for_use(
        rec(valid_until="2026-08-24"),
        project_id="PRJ-HYD-01",
        use=MemoryUse.DECISION_CONTEXT,
    )
    assert out.include is False


def test_superseded_memory_remains_retrievable_for_contradiction_review():
    out = evaluate_memory_for_use(
        rec(MemoryStatus.SUPERSEDED, superseded_by="m2"),
        project_id="PRJ-HYD-01",
        use=MemoryUse.CONTRADICTION_REVIEW,
    )
    assert out.include is True


def test_invalidated_memory_remains_retrievable_for_history_audit():
    out = evaluate_memory_for_use(rec(MemoryStatus.INVALIDATED), project_id="PRJ-HYD-01", use=MemoryUse.HISTORY_AUDIT)
    assert out.include is True
