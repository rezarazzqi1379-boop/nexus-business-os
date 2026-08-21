from dataclasses import dataclass
from typing import Literal, Sequence

from nexus_autonomy.runner import RunnerReport

LedgerStatus = Literal["succeeded", "failed"]


@dataclass(frozen=True)
class OutcomeEvent:
    cycle_id: str
    task_id: str
    status: LedgerStatus
    summary: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeLedger:
    events: tuple[OutcomeEvent, ...] = ()

    def latest_for(self, task_id: str) -> OutcomeEvent | None:
        for event in reversed(self.events):
            if event.task_id == task_id:
                return event
        return None

    def successes(self) -> tuple[OutcomeEvent, ...]:
        return tuple(event for event in self.events if event.status == "succeeded")


def append_report(ledger: OutcomeLedger, cycle_id: str, report: RunnerReport) -> OutcomeLedger:
    if not isinstance(ledger, OutcomeLedger):
        raise TypeError("ledger must be an OutcomeLedger")
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id must be a nonblank string")
    if not isinstance(report, RunnerReport):
        raise TypeError("report must be a RunnerReport")

    appended: list[OutcomeEvent] = list(ledger.events)
    seen = {(event.cycle_id, event.task_id) for event in appended}
    for record in report.executed:
        if record.status == "skipped":
            continue
        key = (cycle_id, record.task_id)
        if key in seen:
            raise ValueError(f"duplicate ledger event for cycle/task: {cycle_id}/{record.task_id}")
        appended.append(
            OutcomeEvent(
                cycle_id=cycle_id,
                task_id=record.task_id,
                status=record.status,
                summary=record.summary,
                evidence_refs=record.evidence_refs,
            )
        )
        seen.add(key)
    return OutcomeLedger(events=tuple(appended))


def completed_task_ids(ledger: OutcomeLedger) -> tuple[str, ...]:
    latest: dict[str, OutcomeEvent] = {}
    for event in ledger.events:
        latest[event.task_id] = event
    return tuple(sorted(task_id for task_id, event in latest.items() if event.status == "succeeded"))
