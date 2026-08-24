from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class EntryOpportunity:
    opportunity_id: str
    company: str
    status: str
    fit: str
    fact: str
    hypothesis: str
    unknowns: tuple[str, ...]
    source_urls: tuple[str, ...]
    route: str
    deadline: date | None = None

    @property
    def is_actionable(self) -> bool:
        return self.status == "open" and (self.deadline is None or self.deadline >= date.today())


def load_entry_map(path: str | Path) -> tuple[EntryOpportunity, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    opportunities = []
    for item in payload["opportunities"]:
        deadline = date.fromisoformat(item["deadline"]) if item.get("deadline") else None
        opportunity = EntryOpportunity(
            opportunity_id=item["opportunity_id"],
            company=item["company"],
            status=item["status"],
            fit=item["fit"],
            fact=item["fact"],
            hypothesis=item["hypothesis"],
            unknowns=tuple(item["unknowns"]),
            source_urls=tuple(item["source_urls"]),
            route=item["route"],
            deadline=deadline,
        )
        if not opportunity.fact or not opportunity.hypothesis or not opportunity.unknowns:
            raise ValueError(f"Incomplete fact/hypothesis/unknown split: {opportunity.opportunity_id}")
        if not all(url.startswith("https://") for url in opportunity.source_urls):
            raise ValueError(f"Non-HTTPS source: {opportunity.opportunity_id}")
        opportunities.append(opportunity)
    return tuple(opportunities)
