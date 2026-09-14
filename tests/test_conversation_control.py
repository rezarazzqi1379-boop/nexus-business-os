import pytest

from conversation_control import (
    ConversationSnapshot, TokenPolicy, allocate_tokens, discover_needs,
    normalize_question, propose_ideas,
)


def snap(**changes):
    values = dict(thread_id="t1", title="NEXUS Audit", summary="", project_id="P1",
                  state="idle", updated_at=100, source_ref="thread:t1")
    values.update(changes)
    return ConversationSnapshot(**values)


def test_token_allocation_preserves_working_and_output_budget():
    result = allocate_tokens(TokenPolicy(), estimated_history=99_000, estimated_evidence=99_000)
    assert result.history + result.evidence + result.working + result.output == 24_000
    assert result.working > 0 and result.output == 4_000


def test_question_normalization_is_compact_and_scoped():
    result = normalize_question("Please just compare the suppliers", project_id="PRJ-KCL-01")
    assert result.startswith("project=PRJ-KCL-01")
    assert "please" not in result.lower()
    assert "preserve_unknowns=true" in result


def test_needs_detect_missing_summary_staleness_and_duplicate_title():
    items = (snap(), snap(thread_id="t2", source_ref="thread:t2", updated_at=200))
    needs = discover_needs(items, now=3_000_000, stale_after=1000)
    kinds = {n.kind for n in needs}
    assert {"evidence_gap", "stale_context", "duplication"}.issubset(kinds)


def test_duplicate_thread_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate_thread_id"):
        discover_needs((snap(), snap()), now=100)


def test_idea_engine_produces_bounded_safe_experiments():
    needs = discover_needs((snap(state="blocked"),), now=100)
    ideas = propose_ideas(needs, max_ideas=2)
    assert len(ideas) == 2
    assert all(i.acceptance_test and i.smallest_experiment for i in ideas)
    assert all(i.auto_runnable for i in ideas)

