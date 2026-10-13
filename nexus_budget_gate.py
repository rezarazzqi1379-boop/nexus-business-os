"""Deterministic budget gate for NEXUS simulation and agent proposals.

No provider billing access or automatic purchases. Monetary budgets are explicit.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class BudgetPolicy:
    monthly_limit_usd: float
    spent_usd: float
    proposed_cost_usd: float
    max_single_experiment_usd: float
    paid_actions_approved: bool = False

def evaluate_budget(policy: BudgetPolicy) -> tuple[bool, tuple[str, ...]]:
    reasons = []
    values = (policy.monthly_limit_usd, policy.spent_usd,
              policy.proposed_cost_usd, policy.max_single_experiment_usd)
    if any(v < 0 or v != v or v == float("inf") for v in values):
        reasons.append("invalid_budget")
    elif policy.proposed_cost_usd > policy.max_single_experiment_usd:
        reasons.append("experiment_cap_exceeded")
    elif policy.spent_usd + policy.proposed_cost_usd > policy.monthly_limit_usd:
        reasons.append("monthly_cap_exceeded")
    if policy.proposed_cost_usd > 0 and not policy.paid_actions_approved:
        reasons.append("paid_action_requires_exact_approval")
    return not reasons, tuple(reasons)
