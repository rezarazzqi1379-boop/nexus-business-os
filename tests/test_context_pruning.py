import pytest

from nexus_core.context_pruning import ContextChunk, select_context


def test_contradiction_and_current_goal_survive_tight_budget():
    chunks = (
        ContextChunk("noise", 40, .99, False, False),
        ContextChunk("current", 20, .7, True, True),
        ContextChunk("conflict", 20, .6, True, True, True),
    )
    selected = select_context(chunks, token_budget=40)
    assert selected == ("conflict", "current")


def test_duplicate_chunks_fail_closed():
    c = ContextChunk("x", 1, .5, True, True)
    with pytest.raises(ValueError):
        select_context((c, c), token_budget=10)


def test_budget_is_hard_limit():
    selected = select_context((ContextChunk("a", 11, 1, True, True),), token_budget=10)
    assert selected == ()
