"""Local, account-free cross-agent shared memory (Walrus-Memory-style, git-native).

Stores durable project decisions, owner preferences, and shared working
context as structured, evidence-backed entries under `.nexus/memory/`, one
JSON-Lines file per namespace. No external account, credential, or network
call is required or made: this module only reads and writes local files,
and those files travel with the repository via git -- which is already
this project's exchange of record between Claude Code, Codex, and any
other AI tool working on it (see AGENTS.md's "Role split").

This is deliberately NOT a chat log. Only distilled, evidence-backed
statements are ever recorded here -- never raw conversation turns. Each
entry carries an explicit provenance (`decided_by`) and optional evidence
references (paths, commit hashes, doc anchors) so a later reader can
verify a claim against the repository itself instead of trusting the
memory text alone, matching this project's evidence-discipline rules (see
the rolling-mill skill, and `collaboration_growth`'s "store derived
metrics and evidence refs, not raw chat").
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
import unicodedata
from contextlib import contextmanager
from functools import wraps
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Literal

Namespace = Literal["preference", "decision", "context"]
_NAMESPACES: tuple[Namespace, ...] = ("preference", "decision", "context")
_MAX_STATEMENT_LENGTH = 2000
_MAX_EVIDENCE_REFS = 20
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialized(method):
    @wraps(method)
    def invoke(self, *args, **kwargs):
        with self._locked():
            return method(self, *args, **kwargs)
    return invoke


def _reject_unsafe_text(value: str, field: str) -> None:
    if _CONTROL_CHARS.search(value):
        raise ValueError(f"invalid_control_characters_in_{field}")
    if any(unicodedata.category(ch) == "Cf" for ch in value):
        raise ValueError(f"invalid_formatting_characters_in_{field}")


@dataclass(frozen=True)
class MemoryEntry:
    entry_id: str
    namespace: Namespace
    statement: str
    decided_by: str
    created_at: str
    project_id: str | None = None
    lane: str | None = None
    evidence_refs: tuple[str, ...] = ()
    superseded_by: str | None = None

    def validate(self) -> None:
        if self.namespace not in _NAMESPACES:
            raise ValueError("invalid_namespace")
        if not self.entry_id.strip():
            raise ValueError("invalid_entry_id")
        if not self.statement.strip():
            raise ValueError("invalid_statement")
        if len(self.statement) > _MAX_STATEMENT_LENGTH:
            raise ValueError("statement_too_long")
        _reject_unsafe_text(self.statement, "statement")
        if not self.decided_by.strip():
            raise ValueError("invalid_decided_by")
        _reject_unsafe_text(self.decided_by, "decided_by")
        if len(self.evidence_refs) > _MAX_EVIDENCE_REFS:
            raise ValueError("too_many_evidence_refs")
        for ref in self.evidence_refs:
            if not ref.strip():
                raise ValueError("invalid_evidence_ref")
            _reject_unsafe_text(ref, "evidence_ref")

    def to_json(self) -> dict:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload

    @classmethod
    def from_json(cls, payload: dict) -> "MemoryEntry":
        return cls(
            entry_id=payload["entry_id"],
            namespace=payload["namespace"],
            statement=payload["statement"],
            decided_by=payload["decided_by"],
            created_at=payload["created_at"],
            project_id=payload.get("project_id"),
            lane=payload.get("lane"),
            evidence_refs=tuple(payload.get("evidence_refs", ())),
            superseded_by=payload.get("superseded_by"),
        )


class ProjectMemoryStore:
    """One JSON-Lines file per namespace under `root` (default `.nexus/memory/`)."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._thread_lock = threading.RLock()
        self._local = threading.local()

    @contextmanager
    def _locked(self):
        """Serialize readers and read-modify-write transactions across processes.

        OS locks release on process exit; the file itself is not a stale lease.
        Nested query calls reuse this instance's current thread transaction.
        """
        with self._thread_lock:
            if getattr(self._local, "locked", False):
                yield
                return
            with (self.root / ".memory.lock").open("a+b") as handle:
                if os.name == "nt":
                    import msvcrt
                    if handle.seek(0, os.SEEK_END) == 0:
                        handle.write(b"0")
                        handle.flush()
                    deadline = time.monotonic() + 15
                    while True:
                        handle.seek(0)
                        try:
                            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                            break
                        except OSError:
                            if time.monotonic() >= deadline:
                                raise TimeoutError("memory_lock_timeout")
                            time.sleep(.01)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                self._local.locked = True
                try:
                    yield
                finally:
                    self._local.locked = False
                    handle.seek(0)
                    if os.name == "nt":
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _append_atomic(self, path: Path, payload: dict) -> None:
        old = path.read_bytes() if path.exists() else b""
        if old and not old.endswith(b"\n"):
            raise ValueError("incomplete_memory_record")
        data = old + (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        fd, temporary = tempfile.mkstemp(prefix=".memory-", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            if os.name != "nt":
                directory = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _path(self, namespace: Namespace) -> Path:
        if namespace not in _NAMESPACES:
            raise ValueError("invalid_namespace")
        return self.root / f"{namespace}.jsonl"

    @_serialized
    def record(
        self,
        namespace: Namespace,
        statement: str,
        *,
        decided_by: str,
        project_id: str | None = None,
        lane: str | None = None,
        evidence_refs: Iterable[str] = (),
        entry_id: str | None = None,
        now: str | None = None,
    ) -> MemoryEntry:
        existing = self.query(namespace=namespace)
        generated_id = entry_id or f"{namespace}-{len(existing) + 1:04d}"
        entry = MemoryEntry(
            entry_id=generated_id,
            namespace=namespace,
            statement=statement,
            decided_by=decided_by,
            created_at=now or _utc_now(),
            project_id=project_id,
            lane=lane,
            evidence_refs=tuple(evidence_refs),
        )
        entry.validate()
        if any(item.entry_id == entry.entry_id for item in existing):
            raise ValueError("duplicate_entry_id")
        path = self._path(namespace)
        self._append_atomic(path, entry.to_json())
        return entry

    @_serialized
    def supersede(self, namespace: Namespace, entry_id: str, *, superseded_by: str) -> None:
        """Mark an entry outdated without deleting it -- history stays, just no longer current."""
        entries = self.query(namespace=namespace)
        if not any(item.entry_id == entry_id for item in entries):
            raise KeyError("unknown_entry_id")
        if not any(item.entry_id == superseded_by for item in entries):
            raise KeyError("unknown_superseding_entry_id")
        original = next(item for item in entries if item.entry_id == entry_id)
        replacement = next(item for item in entries if item.entry_id == superseded_by)
        if (original.project_id, original.lane) != (replacement.project_id, replacement.lane):
            raise ValueError("cross_project_supersession")
        self._append_atomic(self.root / "supersession_events.jsonl", {
            "namespace": namespace, "entry_id": entry_id,
            "superseded_by": superseded_by, "created_at": _utc_now(),
        })

    @_serialized
    def query(
        self,
        *,
        namespace: Namespace | None = None,
        project_id: str | None = None,
        lane: str | None = None,
        include_superseded: bool = True,
    ) -> tuple[MemoryEntry, ...]:
        namespaces = (namespace,) if namespace else _NAMESPACES
        results: list[MemoryEntry] = []
        events_path = self.root / "supersession_events.jsonl"
        supersessions = {}
        if events_path.exists():
            for line in events_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    event = json.loads(line)
                    supersessions[(event["namespace"], event["entry_id"])] = event["superseded_by"]
        for item_namespace in namespaces:
            path = self._path(item_namespace)
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = MemoryEntry.from_json(json.loads(line))
                target = supersessions.get((entry.namespace, entry.entry_id))
                if target:
                    entry = replace(entry, superseded_by=target)
                if project_id is not None and entry.project_id != project_id:
                    continue
                if lane is not None and entry.lane != lane:
                    continue
                if not include_superseded and entry.superseded_by is not None:
                    continue
                results.append(entry)
        return tuple(results)

    def bootstrap_context(
        self,
        *,
        project_id: str | None = None,
        lane: str | None = None,
        limit: int = 20,
    ) -> str:
        """A concise, non-superseded digest for a session to read at start.

        This is the account-free equivalent of Walrus Memory's cross-tool
        context injection: instead of a live hook pushing memory into a
        tool's context automatically, any AI session working on this repo
        (Claude Code, Codex, or otherwise) calls this at the start of
        substantial work and reads the result -- filtered to what is
        still current (not superseded) and to the relevant project/lane
        when given.
        """
        if limit <= 0:
            raise ValueError("invalid_limit")
        sections: list[str] = []
        for item_namespace in _NAMESPACES:
            entries = list(
                self.query(
                    namespace=item_namespace,
                    project_id=project_id,
                    lane=lane,
                    include_superseded=False,
                )
            )
            if not entries:
                continue
            sections.append(f"## {item_namespace}")
            for entry in entries[-limit:]:
                scope = " ".join(
                    part
                    for part in (
                        f"[{entry.project_id}]" if entry.project_id else "",
                        f"({entry.lane})" if entry.lane else "",
                    )
                    if part
                )
                evidence = (
                    f" -- evidence: {', '.join(entry.evidence_refs)}"
                    if entry.evidence_refs
                    else ""
                )
                body = " ".join(part for part in (scope, entry.statement) if part)
                line = f"- {body} (by {entry.decided_by}){evidence}"
                sections.append(line)
        if not sections:
            return "(no recorded project memory yet)"
        return "\n".join(sections)
