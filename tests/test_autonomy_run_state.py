from pathlib import Path

import pytest

from nexus_autonomy.run_state import (
    FileRunnerStateStore,
    RunnerState,
    TaskOutcome,
    apply_runner_report,
    state_from_json,
    state_to_json,
)
from nexus_autonomy.runner import RunRecord, RunnerReport


def _report(*records: RunRecord) -> RunnerReport:
    return RunnerReport(
        executed=records,
        awaiting_approval_task_ids=("approval-1",),
        blocked_task_ids=("blocked-1",),
        deferred_task_ids=("deferred-1",),
        stopped_after_failure=any(record.status == "failed" for record in records),
    )


def test_succeeded_tasks_become_completed_boundary() -> None:
    state = apply_runner_report(
        RunnerState(),
        _report(RunRecord("task-1", "succeeded", "done", ("evidence:1",))),
    )

    assert state.completed_task_ids == ("task-1",)
    assert state.outcomes[0].attempts == 1


def test_failed_tasks_are_retained_but_not_completed() -> None:
    state = apply_runner_report(
        RunnerState(),
        _report(RunRecord("task-1", "failed", "temporary failure", ("log:1",))),
    )

    assert state.completed_task_ids == ()
    assert state.outcomes[0].status == "failed"


def test_retry_increments_attempts_and_can_transition_to_success() -> None:
    failed = apply_runner_report(
        RunnerState(),
        _report(RunRecord("task-1", "failed", "first failure", ())),
    )
    succeeded = apply_runner_report(
        failed,
        _report(RunRecord("task-1", "succeeded", "recovered", ("evidence:2",))),
    )

    assert succeeded.outcomes[0].attempts == 2
    assert succeeded.outcomes[0].status == "succeeded"
    assert succeeded.completed_task_ids == ("task-1",)


def test_skipped_records_do_not_mutate_durable_outcomes() -> None:
    initial = RunnerState(
        outcomes=(TaskOutcome("task-1", "succeeded", "done", (), 1),),
    )
    updated = apply_runner_report(
        initial,
        _report(RunRecord("task-1", "skipped", "already completed", ())),
    )

    assert updated == initial


def test_human_gated_blocked_and_deferred_are_not_marked_complete() -> None:
    state = apply_runner_report(RunnerState(), _report())
    assert state.completed_task_ids == ()
    assert state.outcomes == ()


def test_json_round_trip_is_stable() -> None:
    state = RunnerState(
        outcomes=(TaskOutcome("task-1", "succeeded", "done", ("evidence:1",), 2),),
    )

    encoded = state_to_json(state)
    decoded = state_from_json(encoded)

    assert decoded == state
    assert state_to_json(decoded) == encoded


def test_unknown_fields_fail_closed() -> None:
    with pytest.raises(ValueError, match="unexpected or missing fields"):
        state_from_json('{"version": 1, "outcomes": [], "surprise": true}')


def test_unsupported_version_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported runner state version"):
        state_from_json('{"version": 2, "outcomes": []}')


def test_file_store_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "runtime" / "runner-state.json"
    state = RunnerState(
        outcomes=(TaskOutcome("task-1", "succeeded", "done", ("evidence:1",), 1),),
    )

    FileRunnerStateStore(path).save(state)
    loaded = FileRunnerStateStore(path).load()

    assert loaded == state
    assert loaded.completed_task_ids == ("task-1",)


def test_missing_state_file_bootstraps_empty_state(tmp_path: Path) -> None:
    assert FileRunnerStateStore(tmp_path / "missing.json").load() == RunnerState()
