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


def select_context(chunks: tuple[ContextChunk, ...], *, token_budget: int) -> tuple[str, ...]:
    if token_budget < 0:
        raise ValueError("invalid_budget")
    if len({c.chunk_id for c in chunks}) != len(chunks):
        raise ValueError("duplicate_chunk")
    for c in chunks:
        if not c.chunk_id.strip() or c.tokens < 0 or not 0 <= c.relevance <= 1:
            raise ValueError("invalid_chunk")
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
