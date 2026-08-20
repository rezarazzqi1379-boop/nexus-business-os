from nexus_core.context_pruning import ContextChunk, benchmark_context_pruning


def test_pruning_retains_more_critical_context_than_fifo_at_same_budget():
    chunks = (
        ContextChunk("stale-1", 40, 0.2, False, False),
        ContextChunk("stale-2", 40, 0.1, False, False),
        ContextChunk("evidence", 40, 0.8, True, False),
        ContextChunk("goal", 40, 0.9, False, True),
        ContextChunk("contradiction", 40, 0.7, False, False, True),
    )
    result = benchmark_context_pruning(chunks, token_budget=80)
    assert result.baseline_critical_retained == 0
    assert result.selected_critical_retained == 2
    assert set(result.selected_ids) == {"contradiction", "goal"}


def test_benchmark_reports_token_usage_without_claiming_llm_quality():
    chunks = (
        ContextChunk("a", 60, 0.1, False, False),
        ContextChunk("b", 30, 0.9, True, True),
        ContextChunk("c", 20, 0.8, True, False),
    )
    result = benchmark_context_pruning(chunks, token_budget=60)
    assert result.baseline_tokens == 60
    assert result.selected_tokens == 50
    assert result.token_savings == 10
    assert result.selected_critical_retained == 2
