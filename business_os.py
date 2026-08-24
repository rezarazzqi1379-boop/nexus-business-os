from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from projects import PROJECTS


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
REQUEST_KINDS = frozenset({"research", "draft", "brief", "review", "project_update"})
VAULT_DIRECTORIES = (
    "SYSTEM", "COMPANIES", "PROJECTS", "OPERATIONS", "EVIDENCE", "RESOURCES",
    "QUEUE/pending", "QUEUE/processing", "QUEUE/completed", "QUEUE/failed",
    "GENERATED/briefings", "GENERATED/reports", "GENERATED/drafts", "AUDIT", "TEMPLATES",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


@dataclass(frozen=True)
class VaultRequest:
    request_id: str
    kind: str
    project_id: str
    title: str
    instructions: str
    requested_by: str
    created_at: str

    def validate(self) -> None:
        _safe_id(self.request_id, "request_id")
        if self.kind not in REQUEST_KINDS:
            raise ValueError("invalid_request_kind")
        if self.project_id not in PROJECTS:
            raise ValueError("unknown_project")
        if not all(isinstance(item, str) and item.strip() for item in (
            self.title, self.instructions, self.requested_by, self.created_at
        )):
            raise ValueError("invalid_vault_request")
        if len(self.title) > 200 or len(self.instructions) > 20_000:
            raise ValueError("vault_request_too_large")
        parsed = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("created_at_requires_timezone")

    @property
    def digest(self) -> str:
        self.validate()
        data = json.dumps(self.__dict__, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()


class BusinessOSVault:
    """Provider-neutral Markdown control surface for Obsidian or plain files."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def initialize(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for directory in VAULT_DIRECTORIES:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self._write_once("SYSTEM/README.md", "# NEXUS Vault\n\nProvider-neutral business memory. External writes require exact human approval.\n")

    def _path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("vault_path_escape")
        return candidate

    def _write_once(self, relative: str, content: str) -> Path:
        target = self._path(relative)
        if target.exists():
            return target
        self._atomic_write(target, content)
        return target

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)

    @staticmethod
    def _atomic_create(target: Path, content: str) -> bool:
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            return True
        except FileExistsError:
            return False

    def enqueue(self, request: VaultRequest) -> Path:
        request.validate()
        target = self._path(f"QUEUE/pending/{request.request_id}.json")
        payload = {"schema_version": "nexus.vault-request.v1", **request.__dict__, "digest": request.digest}
        created = self._atomic_create(target, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        if not created:
            existing = json.loads(target.read_text(encoding="utf-8"))
            if existing.get("digest") != request.digest:
                raise ValueError("request_id_collision")
            return target
        self.audit("request_enqueued", request.request_id, {"project_id": request.project_id, "kind": request.kind})
        return target

    def claim(self, request_id: str) -> VaultRequest:
        request_id = _safe_id(request_id, "request_id")
        source = self._path(f"QUEUE/pending/{request_id}.json")
        target = self._path(f"QUEUE/processing/{request_id}.json")
        try:
            os.replace(source, target)
        except FileNotFoundError as exc:
            raise ValueError("request_not_pending") from exc
        value = json.loads(target.read_text(encoding="utf-8"))
        fields = {key: value[key] for key in VaultRequest.__dataclass_fields__}
        request = VaultRequest(**fields)
        if value.get("digest") != request.digest:
            os.replace(target, self._path(f"QUEUE/failed/{request_id}.json"))
            raise ValueError("request_digest_mismatch")
        self.audit("request_claimed", request_id, {"project_id": request.project_id})
        return request

    def complete(self, request: VaultRequest, output: str, *, category: str = "briefings") -> Path:
        request.validate()
        if category not in {"briefings", "reports", "drafts"} or not output.strip():
            raise ValueError("invalid_generated_output")
        processing = self._path(f"QUEUE/processing/{request.request_id}.json")
        if not processing.exists():
            raise ValueError("request_not_processing")
        date = utc_now().date().isoformat()
        generated = self._path(f"GENERATED/{category}/{date}-{request.request_id}.md")
        header = (
            "---\n"
            f"schema_version: nexus.generated.v1\nrequest_id: {request.request_id}\n"
            f"project_id: {request.project_id}\nsource_digest: {request.digest}\n"
            "external_action_authorized: false\n---\n\n"
        )
        self._atomic_write(generated, header + output.strip() + "\n")
        os.replace(processing, self._path(f"QUEUE/completed/{request.request_id}.json"))
        self.audit("request_completed", request.request_id, {"output": str(generated.relative_to(self.root))})
        return generated

    def audit(self, event: str, subject_id: str, details: dict) -> None:
        _safe_id(subject_id, "audit_subject")
        record = {
            "at": utc_now().isoformat(), "event": event, "subject_id": subject_id,
            "details": details,
        }
        path = self._path(f"AUDIT/{utc_now().date().isoformat()}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def status(self) -> dict:
        def count(relative: str, pattern: str) -> int:
            return len(tuple(self._path(relative).glob(pattern)))
        return {
            "schema_version": "nexus.vault-status.v1",
            "pending": count("QUEUE/pending", "*.json"),
            "processing": count("QUEUE/processing", "*.json"),
            "completed": count("QUEUE/completed", "*.json"),
            "failed": count("QUEUE/failed", "*.json"),
            "generated": count("GENERATED", "**/*.md"),
            "external_writes_enabled": False,
        }

    def write_project_index(self) -> Path:
        lines = ["# Project Registry", "", "Generated from the canonical Python registry.", ""]
        for project in sorted(PROJECTS.values(), key=lambda item: (-item.priority, item.project_id)):
            lines.extend((
                f"## {project.project_id}", f"- Status: `{project.status}`", f"- Priority: {project.priority}",
                f"- Objective: {project.objective}", f"- Next evidence: {', '.join(project.next_evidence)}",
                f"- Forbidden: {', '.join(project.forbidden_actions) or 'none'}", "",
            ))
        target = self._path("PROJECTS/_index.md")
        self._atomic_write(target, "\n".join(lines))
        return target

    def generate_daily_pulse(self) -> Path:
        date = utc_now().date().isoformat()
        lines = [f"# Daily Project Pulse - {date}", "", "> Generated locally. No external action authorized.", ""]
        for project in sorted(PROJECTS.values(), key=lambda item: (-item.priority, item.project_id)):
            lines.extend((f"## {project.project_id}", f"- Status: **{project.status}**", f"- Objective: {project.objective}",
                          f"- Evidence needed: {', '.join(project.next_evidence)}", ""))
        target = self._path(f"GENERATED/reports/{date}-daily-project-pulse.md")
        self._atomic_write(target, "\n".join(lines))
        self.audit("daily_pulse_generated", "daily_pulse", {"output": str(target.relative_to(self.root))})
        return target
