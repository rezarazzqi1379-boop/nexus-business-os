from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextChunk:
    chunk_id: str
    tokens: int
    relevance: float
    evidence_bound: bool
    current_goal: bool
    contradiction: bool = False


@dataclass(frozen=True)
class ContextBenchmark:
    token_budget: int
    baseline_tokens: int
    selected_tokens: int
    token_savings: int
    baseline_critical_retained: int
    selected_critical_retained: int
    selected_ids: tuple[str, ...]


def _validate(chunks: tuple[ContextChunk, ...]) -> None:
    if len({c.chunk_id for c in chunks}) != len(chunks):
        raise ValueError("duplicate_chunk")
    for c in chunks:
        if not c.chunk_id.strip() or c.tokens < 0 or not 0 <= c.relevance <= 1:
            raise ValueError("invalid_chunk")


def select_context(chunks: tuple[ContextChunk, ...], *, token_budget: int) -> tuple[str, ...]:
    if token_budget < 0:
        raise ValueError("invalid_budget")
    _validate(chunks)
    ranked = sorted(
        chunks,
        key=lambda c: (
            not c.contradiction,
            not c.current_goal,
            not c.evidence_bound,
            -c.relevance,
            c.tokens,
            c.chunk_id,
        ),
    )
    selected: list[str] = []
    used = 0
    for c in ranked:
        if used + c.tokens <= token_budget:
            selected.append(c.chunk_id)
            used += c.tokens
    return tuple(selected)


def _fifo_baseline(chunks: tuple[ContextChunk, ...], token_budget: int) -> tuple[str, ...]:
    selected: list[str] = []
    used = 0
    for chunk in chunks:
        if used + chunk.tokens <= token_budget:
            selected.append(chunk.chunk_id)
            used += chunk.tokens
    return tuple(selected)


def benchmark_context_pruning(
    chunks: tuple[ContextChunk, ...], *, token_budget: int
) -> ContextBenchmark:
    """Compare evidence-aware pruning with a deterministic FIFO baseline.

    This is intentionally a structural benchmark rather than an LLM-quality claim.
    It measures token use and retention of decision-critical context only.
    """
    if token_budget < 0:
        raise ValueError("invalid_budget")
    _validate(chunks)
    by_id = {c.chunk_id: c for c in chunks}
    baseline = _fifo_baseline(chunks, token_budget)
    selected = select_context(chunks, token_budget=token_budget)

    def tokens(ids: tuple[str, ...]) -> int:
        return sum(by_id[i].tokens for i in ids)

    def critical(ids: tuple[str, ...]) -> int:
        return sum(
            1
            for i in ids
            if by_id[i].contradiction or by_id[i].current_goal or by_id[i].evidence_bound
        )

    baseline_tokens = tokens(baseline)
    selected_tokens = tokens(selected)
    return ContextBenchmark(
        token_budget=token_budget,
        baseline_tokens=baseline_tokens,
        selected_tokens=selected_tokens,
        token_savings=max(0, baseline_tokens - selected_tokens),
        baseline_critical_retained=critical(baseline),
        selected_critical_retained=critical(selected),
        selected_ids=selected,
    )
