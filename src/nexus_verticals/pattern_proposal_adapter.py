"""Adapter from evidence-bounded patterns to PR #19-compatible evolution proposals.

This module creates proposal envelopes only. It does not evaluate candidates, change
agent configuration, merge code, deploy, or grant permissions. The emitted payload
matches the EvolutionProposal field contract in PR #19 so consolidation can later
wire the two branches without hidden schema translation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .pattern_miner import PatternCandidate

PR19_CONTRACT_VERSION = "agent-evolution-v0.1"


@dataclass(frozen=True)
class PatternImprovementProposal:
    proposal_id: str
    component: str
    hypothesis: str
    change_summary: str
    source_observations: tuple[str, ...]
    expected_metric: str
    max_regression: float
    pattern_id: str
    pattern_kind: str
    evidence_refs: tuple[str, ...]
    contract_version: str = PR19_CONTRACT_VERSION

    def as_pr19_payload(self) -> Mapping[str, object]:
        """Return only fields accepted by PR #19 EvolutionProposal."""
        return {
            "proposal_id": self.proposal_id,
            "component": self.component,
            "hypothesis": self.hypothesis,
            "change_summary": self.change_summary,
            "source_observations": self.source_observations,
            "expected_metric": self.expected_metric,
            "max_regression": self.max_regression,
        }


def proposal_from_pattern(
    pattern: PatternCandidate,
    *,
    proposal_id: str,
    component: str,
    hypothesis: str,
    change_summary: str,
    expected_metric: str,
    max_regression: float = 0.0,
) -> PatternImprovementProposal:
    """Create a traceable proposal only from an eligible repeated pattern."""
    if not isinstance(pattern, PatternCandidate):
        raise ValueError("pattern must be PatternCandidate")
    if not pattern.eligible_for_improvement_proposal:
        raise ValueError("pattern is not eligible for an improvement proposal")
    required = {
        "proposal_id": proposal_id,
        "component": component,
        "hypothesis": hypothesis,
        "change_summary": change_summary,
        "expected_metric": expected_metric,
    }
    if any(not isinstance(value, str) or not value.strip() for value in required.values()):
        raise ValueError("proposal fields must be non-empty strings")
    if not isinstance(max_regression, (int, float)) or isinstance(max_regression, bool) or max_regression < 0:
        raise ValueError("max_regression must be a non-negative number")
    if not pattern.observation_ids or not pattern.source_refs:
        raise ValueError("eligible pattern must retain observations and retrievable evidence")

    return PatternImprovementProposal(
        proposal_id=proposal_id.strip(),
        component=component.strip(),
        hypothesis=hypothesis.strip(),
        change_summary=change_summary.strip(),
        source_observations=tuple(pattern.observation_ids),
        expected_metric=expected_metric.strip(),
        max_regression=float(max_regression),
        pattern_id=pattern.pattern_id,
        pattern_kind=pattern.kind,
        evidence_refs=tuple(pattern.source_refs),
    )
