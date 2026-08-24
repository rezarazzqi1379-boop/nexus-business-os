from __future__ import annotations

import hashlib
import re
import sqlite3
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_DOCX_BYTES = 20 * 1024 * 1024
MAX_ZIP_MEMBERS = 2_000
MAX_XML_BYTES = 10 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
MAX_PARAGRAPHS = 100_000
MAX_EXTRACTED_TEXT = 5 * 1024 * 1024


@dataclass(frozen=True)
class CanonicalSource:
    source_id: str
    project_id: str | None
    title: str
    version: str | None
    status: str
    effective_date: str | None
    sha256: str
    content: str


def extract_docx_text(path: Path) -> str:
    if path.suffix.lower() != ".docx":
        raise ValueError("canonical_source_must_be_docx")
    if path.is_symlink() or path.stat().st_size > MAX_DOCX_BYTES:
        raise ValueError("canonical_source_size_or_link_rejected")
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ZIP_MEMBERS:
            raise ValueError("canonical_archive_member_limit")
        try:
            document = archive.getinfo("word/document.xml")
        except KeyError as exc:
            raise ValueError("canonical_document_xml_missing") from exc
        compressed = max(document.compress_size, 1)
        if document.file_size > MAX_XML_BYTES or document.file_size / compressed > MAX_COMPRESSION_RATIO:
            raise ValueError("canonical_archive_expansion_rejected")
        xml = archive.read(document)
        if len(xml) > MAX_XML_BYTES:
            raise ValueError("canonical_xml_size_rejected")
        root = ElementTree.fromstring(xml)
    values = []
    for paragraph in root.iter(f"{W_NS}p"):
        if len(values) >= MAX_PARAGRAPHS:
            raise ValueError("canonical_paragraph_limit")
        value = "".join(node.text or "" for node in paragraph.iter(f"{W_NS}t")).strip()
        if value:
            values.append(value)
    result = "\n".join(values)
    if len(result.encode("utf-8")) > MAX_EXTRACTED_TEXT:
        raise ValueError("canonical_text_limit")
    return result


def _line_value(text: str, label: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        if line.casefold() == label.casefold():
            return lines[index + 1]
    return None


def _match(text: str, pattern: str) -> str | None:
    found = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return found.group(1).strip() if found else None


def parse_source(path: Path) -> CanonicalSource:
    content = extract_docx_text(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    title = content.splitlines()[0]
    source_id = _line_value(content, "Source ID")
    project_id = _line_value(content, "Project ID") or _match(content[:1000], r"(PRJ-[A-Z]+-\d+)")
    version = _line_value(content, "Version") or _match(title, r"\bv([0-9]+(?:\.[0-9]+)+)\b")
    status = _line_value(content, "Status") or "UNCLASSIFIED"
    effective = _line_value(content, "Effective date") or _match(content[:500], r"Effective\s+(\d{1,2}\s+\w+\s+\d{4})")
    if title.startswith("NEXUS MASTER CONTEXT"):
        source_id, status, project_id = "NEXUS-MASTER-CONTEXT", "CANONICAL", None
        effective = effective or _match(content[:500], r"aligned\s+(\d{1,2}\s+\w+\s+\d{4})")
    elif title.startswith("NEXUS SOURCE REGISTRY"):
        source_id, status, project_id = "NEXUS-SOURCE-REGISTRY", "CANONICAL", None
    if not source_id:
        raise ValueError("canonical_source_id_missing")
    return CanonicalSource(source_id, project_id, title, version, status, effective,
                           digest.hexdigest(), content)


class CanonicalStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS canonical_sources (
                source_id TEXT PRIMARY KEY, project_id TEXT, title TEXT NOT NULL, version TEXT,
                status TEXT NOT NULL, effective_date TEXT, sha256 TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL, ingested_at TEXT NOT NULL)""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def ingest(self, path: Path) -> tuple[CanonicalSource, bool]:
        source = parse_source(path.resolve())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT sha256 FROM canonical_sources WHERE source_id=?", (source.source_id,)).fetchone()
            if existing and existing[0] != source.sha256:
                raise ValueError("canonical_source_collision")
            inserted = db.execute(
                "INSERT OR IGNORE INTO canonical_sources VALUES (?,?,?,?,?,?,?,?,?)",
                (source.source_id, source.project_id, source.title, source.version, source.status,
                 source.effective_date, source.sha256, source.content, datetime.now(timezone.utc).isoformat()),
            ).rowcount == 1
        return source, inserted

    def ingest_directory(self, directory: Path) -> list[dict]:
        result = []
        for path in sorted(directory.glob("*.docx")):
            source, inserted = self.ingest(path)
            item = asdict(source)
            item.pop("content")
            result.append({**item, "inserted": inserted})
        return result

    def status(self) -> dict:
        with self._connect() as db:
            rows = db.execute("SELECT source_id,project_id,title,version,status,effective_date,sha256 FROM canonical_sources ORDER BY source_id").fetchall()
        return {"schema_version": "nexus.canonical-status.v1", "count": len(rows), "sources": [dict(row) for row in rows]}

    def latest_for_project(self, project_id: str) -> sqlite3.Row:
        with self._connect() as db:
            row = db.execute("SELECT * FROM canonical_sources WHERE project_id=? ORDER BY ingested_at DESC LIMIT 1", (project_id,)).fetchone()
        if row is None:
            raise KeyError("canonical_project_source_missing")
        return row


def hydrostatic_hold_points(store: CanonicalStore) -> dict:
    row = store.latest_for_project("PRJ-HYD-01")
    rules = (
        ("HYD-PRESSURE", "critical", r"120\s*MPa", "Require a signed geometry-specific pressure capability envelope."),
        ("HYD-THROUGHPUT", "high", r"60\s*pipes/hour", "Bind throughput to FAT geometry, pressure and hold time."),
        ("HYD-CAPABILITY-MATRIX", "high", r"capability matrix", "Obtain the signed pressure-versus-geometry matrix."),
        ("HYD-FAT", "high", r"FAT/TPI/ITP", "Close acceptance criteria before manufacturing release."),
    )
    findings = []
    for code, severity, pattern, required_action in rules:
        found = re.search(pattern, row["content"], re.IGNORECASE)
        if found:
            start, end = max(0, found.start() - 100), min(len(row["content"]), found.end() + 180)
            findings.append({"code": code, "severity": severity, "matched": found.group(0),
                             "evidence_excerpt": " ".join(row["content"][start:end].split()),
                             "required_action": required_action})
    return {"schema_version": "nexus.hydro-audit.v1", "project_id": "PRJ-HYD-01",
            "source_id": row["source_id"], "source_sha256": row["sha256"],
            "external_action_authorized": False, "findings": findings}
