from __future__ import annotations

import hashlib
import re
import sqlite3
import zipfile
from contextlib import closing
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


def _version_tuple(version: str | None) -> tuple[int, ...]:
    if not version:
        return ()
    found = re.fullmatch(r"v?(\d+(?:\.\d+)*)", version.strip(), re.IGNORECASE)
    if not found:
        return ()
    return tuple(int(part) for part in found.group(1).split("."))


def _version_storage_key(version: str | None) -> str:
    return version.strip().lower() if version else "__unversioned__"


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
    """Version-preserving canonical source store.

    v2 keeps historical versions side-by-side. The legacy v1 table is left intact and copied
    forward on first open, so migration is additive and reversible. Active project selection is
    governed by the newest canonical Source Registry declaration, not filesystem or ingest order.
    """

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            with db:
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("""CREATE TABLE IF NOT EXISTS canonical_sources (
                source_id TEXT PRIMARY KEY, project_id TEXT, title TEXT NOT NULL, version TEXT,
                status TEXT NOT NULL, effective_date TEXT, sha256 TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL, ingested_at TEXT NOT NULL)""")
                db.execute("""CREATE TABLE IF NOT EXISTS canonical_source_versions (
                source_id TEXT NOT NULL,
                version_key TEXT NOT NULL,
                project_id TEXT,
                title TEXT NOT NULL,
                version TEXT,
                status TEXT NOT NULL,
                effective_date TEXT,
                sha256 TEXT NOT NULL UNIQUE,
                content TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                PRIMARY KEY (source_id, version_key))""")
                legacy = db.execute(
                    "SELECT source_id,project_id,title,version,status,effective_date,sha256,content,ingested_at "
                    "FROM canonical_sources"
                ).fetchall()
                for row in legacy:
                    db.execute(
                        "INSERT OR IGNORE INTO canonical_source_versions "
                        "(source_id,version_key,project_id,title,version,status,effective_date,sha256,content,ingested_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (row["source_id"], _version_storage_key(row["version"]), row["project_id"], row["title"],
                         row["version"], row["status"], row["effective_date"], row["sha256"], row["content"],
                         row["ingested_at"]),
                    )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def ingest(self, path: Path) -> tuple[CanonicalSource, bool]:
        source = parse_source(path.resolve())
        version_key = _version_storage_key(source.version)
        with closing(self._connect()) as db:
            with db:
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute(
                    "SELECT sha256 FROM canonical_source_versions WHERE source_id=? AND version_key=?",
                    (source.source_id, version_key),
                ).fetchone()
                if existing:
                    if existing["sha256"] != source.sha256:
                        raise ValueError("canonical_source_version_collision")
                    return source, False
                inserted = db.execute(
                    "INSERT INTO canonical_source_versions "
                    "(source_id,version_key,project_id,title,version,status,effective_date,sha256,content,ingested_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (source.source_id, version_key, source.project_id, source.title, source.version, source.status,
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

    def _all_rows(self) -> list[sqlite3.Row]:
        with closing(self._connect()) as db:
            return db.execute(
                "SELECT source_id,project_id,title,version,status,effective_date,sha256,content,ingested_at "
                "FROM canonical_source_versions"
            ).fetchall()

    @staticmethod
    def _highest_version(rows: list[sqlite3.Row]) -> sqlite3.Row:
        if not rows:
            raise KeyError("canonical_source_missing")
        ranked = sorted(rows, key=lambda row: (_version_tuple(row["version"]), row["effective_date"] or "", row["sha256"]),
                        reverse=True)
        top_key = (_version_tuple(ranked[0]["version"]), ranked[0]["effective_date"] or "")
        ties = [row for row in ranked if (_version_tuple(row["version"]), row["effective_date"] or "") == top_key]
        if len(ties) > 1 and len({row["sha256"] for row in ties}) > 1:
            raise ValueError("ambiguous_canonical_source_version")
        return ranked[0]

    def latest_for_source(self, source_id: str) -> sqlite3.Row:
        rows = [row for row in self._all_rows() if row["source_id"] == source_id]
        return self._highest_version(rows)

    def _registry_declared_version(self, source_id: str) -> str | None:
        try:
            registry = self.latest_for_source("NEXUS-SOURCE-REGISTRY")
        except KeyError:
            return None
        lines = [line.strip() for line in registry["content"].splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line != source_id:
                continue
            if index + 2 >= len(lines):
                return None
            status = lines[index + 1].casefold()
            if not status.startswith("canonical"):
                return None
            canonical_file = lines[index + 2]
            return _match(canonical_file, r"v([0-9]+(?:\.[0-9]+)+)")
        return None

    def status(self) -> dict:
        rows = self._all_rows()
        sources = []
        for row in sorted(rows, key=lambda item: (item["source_id"], _version_tuple(item["version"]))):
            item = {key: row[key] for key in ("source_id", "project_id", "title", "version", "status",
                                               "effective_date", "sha256")}
            declared = self._registry_declared_version(row["source_id"])
            item["active"] = bool(declared and row["version"] == declared)
            if row["source_id"] == "NEXUS-SOURCE-REGISTRY":
                item["active"] = row["sha256"] == self.latest_for_source("NEXUS-SOURCE-REGISTRY")["sha256"]
            elif row["source_id"] == "NEXUS-MASTER-CONTEXT" and declared is None:
                item["active"] = row["sha256"] == self.latest_for_source("NEXUS-MASTER-CONTEXT")["sha256"]
            sources.append(item)
        return {"schema_version": "nexus.canonical-status.v2", "count": len(rows), "sources": sources}

    def latest_for_project(self, project_id: str) -> sqlite3.Row:
        rows = [row for row in self._all_rows() if row["project_id"] == project_id]
        if not rows:
            raise KeyError("canonical_project_source_missing")
        selected: list[sqlite3.Row] = []
        for source_id in sorted({row["source_id"] for row in rows}):
            source_rows = [row for row in rows if row["source_id"] == source_id]
            declared = self._registry_declared_version(source_id)
            if declared:
                matches = [row for row in source_rows if row["version"] == declared]
                if len(matches) != 1:
                    raise KeyError(f"registry_declared_source_version_missing:{source_id}:{declared}")
                selected.append(matches[0])
            elif len(source_rows) == 1:
                selected.append(source_rows[0])
            else:
                raise KeyError(f"registry_declaration_required_for_versioned_source:{source_id}")
        if not selected:
            raise KeyError(f"project_not_declared_canonical_in_registry:{project_id}")
        if len(selected) != 1:
            raise ValueError(f"ambiguous_canonical_project_source:{project_id}")
        return selected[0]


_CAPABILITY_MATRIX_NEGATION = (
    r"(?:no|not|cannot|can't|unable to|without|will not|won't|declin(?:e[sd]?|ing)|reject(?:ed|s)?)"
    r"[^.\n]{0,60}capability matrix"
    r"|capability matrix[^.\n]{0,60}(?:not available|unavailable|cannot be provided|will not be provided|"
    r"is declined|not possible)"
)

_FAT_NEGATION = (
    r"(?:no|not|cannot|can't|unable to|without|will not|won't|declin(?:e[sd]?|ing)|reject(?:ed|s)?)"
    r"[^.\n]{0,60}(?:FAT/TPI/ITP|FAT|TPI|ITP)"
    r"|(?:FAT/TPI/ITP|FAT|TPI|ITP)[^.\n]{0,60}(?:not available|unavailable|cannot be provided|"
    r"will not be provided|is declined|not possible)"
)

# Each rule is (code, severity, buyer_pattern, required_action, contradiction_kind, contradiction_spec).
# contradiction_kind "numeric" pairs a value-extraction regex with the buyer's expected value: a supplier
# statement citing a *different* value for the same unit is an explicit, conservative contradiction signal.
# contradiction_kind "keyword" pairs an explicit negation regex: only an explicit decline/unavailability
# statement counts as a contradiction -- mere silence on the topic is never inferred as one.
HYD_HOLD_POINT_RULES = (
    ("HYD-PRESSURE", "critical", r"120\s*MPa", "Require a signed geometry-specific pressure capability envelope.",
     "numeric", {"value_pattern": r"(\d+(?:\.\d+)?)\s*MPa", "expected_value": "120"}),
    ("HYD-THROUGHPUT", "high", r"60\s*pipes/hour", "Bind throughput to FAT geometry, pressure and hold time.",
     "numeric", {"value_pattern": r"(\d+(?:\.\d+)?)\s*pipes\s*/\s*hour", "expected_value": "60"}),
    ("HYD-CAPABILITY-MATRIX", "high", r"capability matrix", "Obtain the signed pressure-versus-geometry matrix.",
     "keyword", {"negation_pattern": _CAPABILITY_MATRIX_NEGATION}),
    ("HYD-FAT", "high", r"FAT/TPI/ITP", "Close acceptance criteria before manufacturing release.",
     "keyword", {"negation_pattern": _FAT_NEGATION}),
)


def hydrostatic_hold_points(store: CanonicalStore) -> dict:
    row = store.latest_for_project("PRJ-HYD-01")
    findings = []
    for code, severity, pattern, required_action, _kind, _spec in HYD_HOLD_POINT_RULES:
        found = re.search(pattern, row["content"], re.IGNORECASE)
        if found:
            start, end = max(0, found.start() - 100), min(len(row["content"]), found.end() + 180)
            findings.append({"code": code, "severity": severity, "matched": found.group(0),
                             "evidence_excerpt": " ".join(row["content"][start:end].split()),
                             "required_action": required_action})
    return {"schema_version": "nexus.hydro-audit.v1", "project_id": "PRJ-HYD-01",
            "source_id": row["source_id"], "source_sha256": row["sha256"],
            "external_action_authorized": False, "findings": findings}
