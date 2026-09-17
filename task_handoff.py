"""Dual-AI task handoff: minimum structured-file infrastructure for
Claude Code <-> ChatGPT/NEXUS coordination over shared GitHub state.

No custom message bus. A handoff is a versioned JSON record written to
``.nexus/handoffs/<task_id>.json`` in the repository -- the file itself,
plus git's own branch/commit history, is the shared state. "One task, one
branch" and "base/head SHA binding" are conventions this module records
but does not itself enforce (git already enforces branch identity).
"No duplicate AI execution" is enforced here: claiming a task_id already
held by a different owner in a non-terminal state raises ``HandoffConflict``.
Crash/quota recovery is a property of persistence: any process can call
``HandoffStore.read`` to resume from the last durable state.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar

from contracts import canonical_digest

SCHEMA_VERSION = "nexus.task-handoff.v1"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SHA_HEX = re.compile(r"^[0-9a-f]{40}$")

STATES = frozenset({"CLAIMED", "IN_PROGRESS", "TESTS_PASSED", "BLOCKED", "READY_FOR_REVIEW", "DONE"})
TERMINAL_STATES = frozenset({"DONE", "BLOCKED"})
RISK_CLASSES = frozenset({"LOW", "MEDIUM", "HIGH"})
OWNERS = frozenset({"claude-code", "chatgpt-nexus", "human"})
HANDOFF_SUBDIR = Path(".nexus") / "handoffs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid_{field_name}")
    return value


def _sha(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not SHA_HEX.fullmatch(value):
        raise ValueError(f"invalid_{field_name}")
    return value


@dataclass(frozen=True)
class TestEvidence:
    # This is a domain record, not a pytest test container.
    __test__: ClassVar[bool] = False
    command: str
    exit_code: int
    passed: int
    failed: int
    errors: int
    skipped: int

    def validate(self) -> None:
        if not self.command.strip():
            raise ValueError("invalid_test_command")
        for value in (self.exit_code, self.passed, self.failed, self.errors, self.skipped):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("invalid_test_evidence_count")


@dataclass(frozen=True)
class TaskHandoff:
    task_id: str
    owner: str
    branch: str
    base_sha: str
    head_sha: str
    state: str
    risk_class: str
    review_round: int
    protected_action_required: bool
    next_deterministic_action: str
    project_id: str | None = None
    lane_id: str | None = None
    files_changed: tuple[str, ...] = ()
    tests_run: tuple[TestEvidence, ...] = ()
    claims: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    cross_project_touch: bool = False
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        _safe_id(self.task_id, "task_id")
        if self.owner not in OWNERS:
            raise ValueError("invalid_owner")
        if not self.branch.strip():
            raise ValueError("invalid_branch")
        _sha(self.base_sha, "base_sha")
        _sha(self.head_sha, "head_sha")
        if self.state not in STATES:
            raise ValueError("invalid_state")
        if self.risk_class not in RISK_CLASSES:
            raise ValueError("invalid_risk_class")
        if isinstance(self.review_round, bool) or not isinstance(self.review_round, int) or self.review_round < 1:
            raise ValueError("invalid_review_round")
        if not isinstance(self.protected_action_required, bool):
            raise ValueError("invalid_protected_action_required")
        if not isinstance(self.cross_project_touch, bool):
            raise ValueError("invalid_cross_project_touch")
        if not self.next_deterministic_action.strip():
            raise ValueError("invalid_next_deterministic_action")
        if len(set(self.files_changed)) != len(self.files_changed):
            raise ValueError("duplicate_files_changed")
        for item in self.tests_run:
            item.validate()

    @property
    def digest(self) -> str:
        self.validate()
        return canonical_digest(asdict(self))


class HandoffConflict(ValueError):
    """A task_id is already claimed by a different owner in a non-terminal state."""


class HandoffStore:
    """File-backed handoff registry: one JSON file per task_id under ``.nexus/handoffs/``.

    This is the shared state itself -- committing the file is how one AI hands a task
    to the other over GitHub, per the mission's "prefer structured files, not a message bus."
    """

    def __init__(self, root: Path) -> None:
        self.root = (root / HANDOFF_SUBDIR).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self.root / f"{_safe_id(task_id, 'task_id')}.json"

    def read(self, task_id: str) -> TaskHandoff | None:
        path = self._path(task_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw.pop("digest", None)
        raw["tests_run"] = tuple(TestEvidence(**item) for item in raw.get("tests_run", ()))
        for key in ("files_changed", "claims", "evidence_refs", "unknowns"):
            raw[key] = tuple(raw.get(key, ()))
        return TaskHandoff(**raw)

    def claim(self, handoff: TaskHandoff) -> Path:
        """Create or take over a task. Refuses another owner's live (non-terminal) claim."""
        handoff.validate()
        existing = self.read(handoff.task_id)
        if existing is not None and existing.owner != handoff.owner and existing.state not in TERMINAL_STATES:
            raise HandoffConflict(f"task_already_claimed_by:{existing.owner}:state:{existing.state}")
        return self._write(handoff)

    def update(self, handoff: TaskHandoff) -> Path:
        """Advance an existing handoff. Refuses to write over a different owner's record."""
        handoff.validate()
        existing = self.read(handoff.task_id)
        if existing is None:
            raise KeyError("unknown_task_handoff")
        if existing.owner != handoff.owner:
            raise HandoffConflict(f"task_owned_by:{existing.owner}")
        return self._write(handoff)

    def _write(self, handoff: TaskHandoff) -> Path:
        path = self._path(handoff.task_id)
        payload = asdict(handoff)
        payload["digest"] = handoff.digest
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        return path
