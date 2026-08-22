"""Outcome Density contract for NEXUS shadow measurement.

The contract stores raw denominators first. Ratios are derived only when their
source denominator is non-zero; missing observations remain None rather than
being converted into fake precision.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OutcomeFunnel:
    signals: int = 0
    valid_problems: int = 0
    qualified_opportunities: int = 0
    approved_actions: int = 0
    replies: int = 0
    rfqs: int = 0
    quotes: int = 0
    orders: int = 0

    def validate(self) -> list[str]:
        errors: list[str] = []
        fields = (
            "signals", "valid_problems", "qualified_opportunities", "approved_actions",
            "replies", "rfqs", "quotes", "orders",
        )
        for name in fields:
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{name} must be a non-negative integer")
        # The funnel is observational; downstream counts cannot exceed their upstream pool.
        pairs = (
            ("valid_problems", "signals"),
            ("qualified_opportunities", "valid_problems"),
            ("approved_actions", "qualified_opportunities"),
            ("replies", "approved_actions"),
            ("rfqs", "replies"),
            ("quotes", "rfqs"),
            ("orders", "quotes"),
        )
        for child, parent in pairs:
            if getattr(self, child) > getattr(self, parent):
                errors.append(f"{child} cannot exceed {parent}")
        return errors

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float | None:
        if denominator == 0:
            return None
        return numerator / denominator

    def rates(self) -> dict[str, float | None]:
        if self.validate():
            raise ValueError("invalid outcome funnel")
        return {
            "problem_per_signal": self._rate(self.valid_problems, self.signals),
            "opportunity_per_problem": self._rate(self.qualified_opportunities, self.valid_problems),
            "action_per_opportunity": self._rate(self.approved_actions, self.qualified_opportunities),
            "reply_per_action": self._rate(self.replies, self.approved_actions),
            "rfq_per_reply": self._rate(self.rfqs, self.replies),
            "quote_per_rfq": self._rate(self.quotes, self.rfqs),
            "order_per_quote": self._rate(self.orders, self.quotes),
        }
