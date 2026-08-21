from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

from nexus_autonomy.runner import RunnerReport


_STATE_VERSION = 1
PersistedStatus = Literal["succeeded", "failed"]


@dataclass(frozen=True)
class TaskOutcome:
    task_id: str
    status: PersistedStatus
    summary: str
    evidence_refs: tuple[str, ...]
    attempts: int


@dataclass(frozen=True)
class RunnerState:
    version: int = _STATE_VERSION
    outcomes: tuple[TaskOutcome, ...] = ()

    @property
    def completed_task_ids(self) -> tuple[str, ...]:
        return tuple(
            outcome.task_id for outcome in self.outcomes if outcome.status == "succeeded"
        )


def _validate_state(state: RunnerState) -> None:
    if not isinstance(state, RunnerState):
        raise TypeError("state must be a RunnerState")
    if state.version != _STATE_VERSION:
        raise ValueError(f"unsupported runner state version: {state.version}")

    seen: set[str] = set()
    for outcome in state.outcomes:
        if not isinstance(outcome, TaskOutcome):
            raise TypeError("state outcomes must contain TaskOutcome values")
        if not isinstance(outcome.task_id, str) or not outcome.task_id.strip():
            raise ValueError("outcome task_id must be a nonblank string")
        if outcome.task_id in seen:
            raise ValueError(f"duplicate outcome task_id: {outcome.task_id}")
        seen.add(outcome.task_id)
        if outcome.status not in {"succeeded", "failed"}:
            raise ValueError("unsupported persisted outcome status")
        if not isinstance(outcome.summary, str) or not outcome.summary.strip():
            raise ValueError("outcome summary must be a nonblank string")
        if not isinstance(outcome.evidence_refs, tuple):
            raise ValueError("outcome evidence_refs must be a tuple")
        if any(not isinstance(ref, str) or not ref.strip() for ref in outcome.evidence_refs):
            raise ValueError("outcome evidence_refs must contain nonblank strings")
        if not isinstance(outcome.attempts, int) or isinstance(outcome.attempts, bool) or outcome.attempts < 1:
            raise ValueError("outcome attempts must be a positive integer")


def apply_runner_report(state: RunnerState, report: RunnerReport) -> RunnerState:
    """Fold one runner report into durable state without treating skips as outcomes.

    Succeeded tasks become the idempotency boundary for later cycles. Failed tasks are
    retained with their latest evidence/summary and incremented attempt count so retry
    policy can be added without losing history. Human-gated, blocked and deferred work
    is deliberately not marked complete.
    """
    _validate_state(state)
    if not isinstance(report, RunnerReport):
        raise TypeError("report must be a RunnerReport")

    by_id = {outcome.task_id: outcome for outcome in state.outcomes}
    for record in report.executed:
        if record.status == "skipped":
            continue
        previous = by_id.get(record.task_id)
        attempts = 1 if previous is None else previous.attempts + 1
        by_id[record.task_id] = TaskOutcome(
            task_id=record.task_id,
            status=record.status,
            summary=record.summary,
            evidence_refs=record.evidence_refs,
            attempts=attempts,
        )

    updated = RunnerState(
        version=_STATE_VERSION,
        outcomes=tuple(by_id[task_id] for task_id in sorted(by_id)),
    )
    _validate_state(updated)
    return updated


def state_to_json(state: RunnerState) -> str:
    _validate_state(state)
    payload = {
        "version": state.version,
        "outcomes": [
            {
                **asdict(outcome),
                "evidence_refs": list(outcome.evidence_refs),
            }
            for outcome in state.outcomes
        ],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def state_from_json(raw: str) -> RunnerState:
    if not isinstance(raw, str):
        raise TypeError("raw state must be a string")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("runner state is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("runner state root must be an object")
    if set(payload) != {"version", "outcomes"}:
        raise ValueError("runner state has unexpected or missing fields")
    outcomes_raw = payload["outcomes"]
    if not isinstance(outcomes_raw, list):
        raise ValueError("runner state outcomes must be a list")

    outcomes: list[TaskOutcome] = []
    for value in outcomes_raw:
        if not isinstance(value, dict):
            raise ValueError("runner state outcome must be an object")
        if set(value) != {"task_id", "status", "summary", "evidence_refs", "attempts"}:
            raise ValueError("runner state outcome has unexpected or missing fields")
        refs = value["evidence_refs"]
        if not isinstance(refs, list):
            raise ValueError("runner state evidence_refs must be a list")
        outcomes.append(
            TaskOutcome(
                task_id=value["task_id"],
                status=value["status"],
                summary=value["summary"],
                evidence_refs=tuple(refs),
                attempts=value["attempts"],
            )
        )

    state = RunnerState(version=payload["version"], outcomes=tuple(outcomes))
    _validate_state(state)
    return state


class FileRunnerStateStore:
    """Small provider-neutral filesystem backend using atomic same-directory replace."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> RunnerState:
        if not self.path.exists():
            return RunnerState()
        if not self.path.is_file():
            raise ValueError("runner state path must be a file")
        return state_from_json(self.path.read_text(encoding="utf-8"))

    def save(self, state: RunnerState) -> None:
        serialized = state_to_json(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: str | None = None
        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = handle.name
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
            temp_path = None
        finally:
            if temp_path is not None:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
