"""Runner-agnostic, evidence-gated task supervision for NEXUS.

Runner state is treated as an observation only.  In particular, ``done`` and
``idle`` never prove that a task is acceptable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from time import time


class Phase(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    PRODUCED = "produced"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"


@dataclass(frozen=True)
class AcceptanceContract:
    project_id: str
    expected_packet_digest: str
    required_tests: tuple[str, ...]
    required_evidence: tuple[str, ...]
    max_runtime_seconds: int = 1800
    max_cost_units: int = 100
    requires_human_approval: bool = False


@dataclass(frozen=True)
class ArtifactClaim:
    project_id: str
    packet_digest: str
    artifact: bytes
    evidence: tuple[str, ...]
    passed_tests: tuple[str, ...]
    human_approved: bool = False

    @property
    def artifact_digest(self) -> str:
        return sha256(self.artifact).hexdigest()


@dataclass
class TaskRecord:
    task_id: str
    contract: AcceptanceContract
    phase: Phase = Phase.QUEUED
    started_at: float | None = None
    cost_units: int = 0
    seen_observations: set[str] = field(default_factory=set)
    reasons: list[str] = field(default_factory=list)


class Supervisor:
    """Deterministic boundary between a runner and project acceptance."""

    _WORKING = {"working", "running"}
    _BLOCKED = {"blocked", "waiting"}
    _PRODUCED = {"done", "idle"}

    def observe(
        self,
        task: TaskRecord,
        *,
        observation_id: str,
        runner_state: str,
        now: float | None = None,
        cost_delta: int = 0,
    ) -> Phase:
        if observation_id in task.seen_observations:
            return task.phase
        task.seen_observations.add(observation_id)
        now = time() if now is None else now
        task.started_at = now if task.started_at is None else task.started_at
        task.cost_units += max(0, cost_delta)

        if now - task.started_at > task.contract.max_runtime_seconds:
            return self._fail(task, "runtime_budget_exhausted")
        if task.cost_units > task.contract.max_cost_units:
            return self._fail(task, "cost_budget_exhausted")

        state = runner_state.strip().lower()
        if state in self._WORKING:
            task.phase = Phase.RUNNING
        elif state in self._BLOCKED:
            task.phase = Phase.BLOCKED
            task.reasons.append("human_decision_required")
        elif state in self._PRODUCED:
            task.phase = Phase.PRODUCED
        else:
            task.phase = Phase.BLOCKED
            task.reasons.append("unknown_runner_state")
        return task.phase

    def verify(self, task: TaskRecord, claim: ArtifactClaim) -> Phase:
        """Accept only a complete claim bound to the exact task contract."""
        failures: list[str] = []
        c = task.contract
        if task.phase is not Phase.PRODUCED:
            failures.append("runner_has_not_produced")
        if claim.project_id != c.project_id:
            failures.append("cross_project_artifact")
        if claim.packet_digest != c.expected_packet_digest:
            failures.append("packet_digest_mismatch")
        if not claim.artifact:
            failures.append("empty_artifact")
        if not set(c.required_evidence).issubset(claim.evidence):
            failures.append("missing_evidence")
        if not set(c.required_tests).issubset(claim.passed_tests):
            failures.append("missing_or_failed_tests")
        if c.requires_human_approval and not claim.human_approved:
            failures.append("human_approval_missing")

        if failures:
            task.phase = Phase.REJECTED
            task.reasons.extend(failures)
        else:
            task.phase = Phase.ACCEPTED
        return task.phase

    @staticmethod
    def _fail(task: TaskRecord, reason: str) -> Phase:
        task.phase = Phase.FAILED
        task.reasons.append(reason)
        return task.phase
