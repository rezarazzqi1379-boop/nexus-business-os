import pytest

from nexus_autonomy.outcome_ledger import OutcomeLedger, append_report, completed_task_ids
from nexus_autonomy.runner import RunRecord, RunnerReport


def report(*records):
    return RunnerReport(tuple(records), (), (), (), False)


def test_appends_non_skipped_events_and_projects_successes():
    ledger = append_report(
        OutcomeLedger(),
        "cycle-1",
        report(
            RunRecord("a", "succeeded", "ok", ("ref:a",)),
            RunRecord("b", "failed", "bad", ("ref:b",)),
            RunRecord("c", "skipped", "done", ()),
        ),
    )
    assert [event.task_id for event in ledger.events] == ["a", "b"]
    assert completed_task_ids(ledger) == ("a",)


def test_latest_event_controls_completed_projection():
    first = append_report(OutcomeLedger(), "cycle-1", report(RunRecord("a", "failed", "bad", ())))
    second = append_report(first, "cycle-2", report(RunRecord("a", "succeeded", "ok", ("ref:a",))))
    assert second.latest_for("a").status == "succeeded"
    assert completed_task_ids(second) == ("a",)


def test_duplicate_cycle_task_is_rejected():
    first = append_report(OutcomeLedger(), "cycle-1", report(RunRecord("a", "failed", "bad", ())))
    with pytest.raises(ValueError, match="duplicate ledger event"):
        append_report(first, "cycle-1", report(RunRecord("a", "succeeded", "ok", ())))


def test_blank_cycle_id_is_rejected():
    with pytest.raises(ValueError):
        append_report(OutcomeLedger(), " ", report())
