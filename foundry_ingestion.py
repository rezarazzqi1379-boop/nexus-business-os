"""Governed factory-data ingestion for the Expert Foundry.

Reads a factory evidence file (CSV, XLSX or JSON), validates it against a strict
row schema, and writes normalized, reviewable records into an ExpertFoundryStore.
It never touches the original file, never assigns a unit it cannot verify, never
crosses project boundaries, and never promotes a claim or proposes a recipe or
setpoint. Equipment integration, live outreach and autonomous promotion are all
out of scope by construction: this module only ever calls ExpertFoundryStore.append().

XLSX support is a minimal, dependency-free OOXML reader (zipfile + XML) limited to
the first worksheet's raw cell values -- no formulas, no merged cells, no Excel
date serials. Timestamps must be written as ISO-8601 text in every format.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import stat
import sys
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree

from expert_foundry import (
    SAFE_ID,
    ExperienceRecord,
    ExpertFoundryStore,
    HypothesisRecord,
    KnowledgeRecord,
)

if sys.platform == "win32":
    import msvcrt
    import time as _time

    def _acquire_lock(handle) -> None:
        handle.seek(0)
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                _time.sleep(0.005)

    def _release_lock(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _acquire_lock(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


CATEGORIES = frozenset({"MEASUREMENT", "OPERATOR_OBSERVATION", "INTERPRETATION", "HYPOTHESIS"})
REQUIRED_COMMON_FIELDS = (
    "project_id", "heat_id", "category", "field", "value", "unit", "timestamp",
    "source_locator", "statement",
)
NON_MEASUREMENT_UNIT = "n/a"
MEASUREMENT_UNITS = frozenset({
    "degC", "degF", "K", "mm", "cm", "m", "kg", "g", "t", "s", "min", "h",
    "wt%", "at%", "ppm", "ppb", "kA", "A", "V", "Pa", "kPa", "MPa", "bar", "kg/m3", "N",
})
AMBIGUOUS_UNITS = frozenset({
    "deg", "%", "T", "oz", "ton", "lb", "F", "C", "temp", "unit", "units", "degrees",
})
DEFAULT_OBSERVATION_CONFIDENCE = 0.5
DEFAULT_INTERPRETATION_CONFIDENCE = 0.3


class IngestionSchemaError(ValueError):
    """Raised for whole-batch failures: malformed input, unsupported format,
    cross-project references, or a tampered raw-evidence vault. Nothing is
    written to the store or the vault when this is raised."""


def _isoformat_utc(value: str, field_name: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field_name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _stamp_locator(locator: str, ingestion_timestamp: str, raw_file_sha256: str) -> str:
    return f"{locator}|raw_sha256={raw_file_sha256}|ingested_at={ingestion_timestamp}"


def _content_hash(*, project_id: str, heat_id: str, category: str, field_name: str,
                   value: str, unit: str, timestamp: str, statement: str) -> str:
    canonical = json.dumps(
        {
            "project_id": project_id, "heat_id": heat_id, "category": category,
            "field": field_name, "value": value, "unit": unit,
            "timestamp": timestamp, "statement": statement,
        },
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


_RECORD_ID_PREFIX = {
    "MEASUREMENT": "meas", "OPERATOR_OBSERVATION": "obs",
    "INTERPRETATION": "interp", "HYPOTHESIS": "hyp",
}


# --------------------------------------------------------------------------
# File parsing: CSV, JSON and a minimal dependency-free XLSX reader.
# --------------------------------------------------------------------------

def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".xlsx":
        return "xlsx"
    if suffix == ".json":
        return "json"
    raise IngestionSchemaError(f"unsupported_file_extension:{suffix or 'none'}")


def parse_csv_rows(raw_bytes: bytes) -> list[dict]:
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionSchemaError("invalid_csv_encoding") from exc
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise IngestionSchemaError("csv_missing_header_row")
    rows = []
    for raw_row in reader:
        row = {}
        for key, cell in raw_row.items():
            if key is None:
                continue
            row[key.strip()] = cell.strip() if isinstance(cell, str) else cell
        rows.append(row)
    return rows


def parse_json_rows(raw_bytes: bytes) -> tuple[dict, list[dict]]:
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionSchemaError("malformed_json") from exc
    if isinstance(payload, list):
        rows = payload
        meta: dict = {}
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        rows = payload["rows"]
        meta = {key: value for key, value in payload.items() if key != "rows"}
    else:
        raise IngestionSchemaError("json_must_be_row_list_or_object_with_rows")
    if not all(isinstance(row, dict) for row in rows):
        raise IngestionSchemaError("json_rows_must_be_objects")
    normalized = []
    for row in rows:
        normalized.append({
            key: (str(value) if value is not None else "") for key, value in row.items()
        })
    return meta, normalized


_XLSX_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _column_letters_to_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch.upper()) - ord("A") + 1)
    return index - 1


def parse_xlsx_rows(raw_bytes: bytes) -> list[dict]:
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
            names = archive.namelist()
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in names:
                shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                for item in shared_root.findall("m:si", _XLSX_NS):
                    text = "".join(node.text or "" for node in item.findall(".//m:t", _XLSX_NS))
                    shared_strings.append(text)
            sheet_path = "xl/worksheets/sheet1.xml"
            if sheet_path not in names:
                raise IngestionSchemaError("xlsx_missing_first_worksheet")
            sheet_root = ElementTree.fromstring(archive.read(sheet_path))
            grid: list[dict[int, str]] = []
            for row_el in sheet_root.findall(".//m:sheetData/m:row", _XLSX_NS):
                cells: dict[int, str] = {}
                for cell_el in row_el.findall("m:c", _XLSX_NS):
                    col_index = _column_letters_to_index(cell_el.get("r", ""))
                    cell_type = cell_el.get("t")
                    value_el = cell_el.find("m:v", _XLSX_NS)
                    if cell_type == "s" and value_el is not None and value_el.text is not None:
                        value = shared_strings[int(value_el.text)]
                    elif cell_type == "inlineStr":
                        inline = cell_el.find(".//m:t", _XLSX_NS)
                        value = inline.text or "" if inline is not None else ""
                    elif value_el is not None:
                        value = value_el.text or ""
                    else:
                        value = ""
                    cells[col_index] = value
                grid.append(cells)
    except zipfile.BadZipFile as exc:
        raise IngestionSchemaError("malformed_xlsx") from exc
    except ElementTree.ParseError as exc:
        raise IngestionSchemaError("malformed_xlsx_xml") from exc
    if not grid:
        return []
    header_row = grid[0]
    width = max(header_row.keys(), default=-1) + 1
    headers = [header_row.get(i, "").strip() for i in range(width)]
    rows = []
    for raw_row in grid[1:]:
        if not raw_row:
            continue
        row = {headers[i]: raw_row.get(i, "") for i in range(width) if headers[i]}
        rows.append(row)
    return rows


def parse_rows(path: Path, raw_bytes: bytes) -> tuple[dict, list[dict]]:
    file_format = detect_format(path)
    if file_format == "csv":
        return {}, parse_csv_rows(raw_bytes)
    if file_format == "json":
        return parse_json_rows(raw_bytes)
    return {}, parse_xlsx_rows(raw_bytes)


# --------------------------------------------------------------------------
# Raw evidence vault: original bytes are hashed, never mutated, write-once.
# --------------------------------------------------------------------------

class RawEvidenceVault:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _vault_path(self, file_sha256: str, suffix: str) -> Path:
        return self.root / f"{file_sha256}{suffix}"

    def verify(self, file_sha256: str, suffix: str) -> None:
        """Raise if a previously vaulted copy no longer matches its own filename hash."""
        path = self._vault_path(file_sha256, suffix)
        if not path.exists():
            return
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != file_sha256:
            raise IngestionSchemaError(f"raw_evidence_vault_tampered:{path.name}")

    def store(self, raw_bytes: bytes, file_sha256: str, suffix: str) -> Path:
        """Write-once copy of the original bytes. Idempotent on identical content;
        never overwrites, and refuses to proceed if the vault was tampered with."""
        self.verify(file_sha256, suffix)
        target = self._vault_path(file_sha256, suffix)
        if target.exists():
            return target
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw_bytes)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        try:
            os.chmod(target, stat.S_IREAD)
        except OSError:
            pass
        return target


# --------------------------------------------------------------------------
# Row-level schema validation and normalization.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class NormalizedRow:
    row_index: int
    record_id: str
    category: str
    project_id: str
    heat_id: str
    field_name: str
    value: str
    unit: str
    timestamp: str
    source_locator: str
    statement: str
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RowOutcome:
    row_index: int
    status: str  # ACCEPTED | REJECTED | DUPLICATE
    category: str | None
    record_id: str | None
    reason: str | None


def _clean(row: dict, key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return value.strip() if isinstance(value, str) else str(value).strip()


def _pipe_list(row: dict, key: str) -> tuple[str, ...]:
    raw = _clean(row, key)
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split("|") if part.strip())


def _validate_common(row: dict, row_index: int, expected_project_id: str) -> None:
    missing = [name for name in REQUIRED_COMMON_FIELDS if not _clean(row, name)]
    if missing:
        raise ValueError(f"missing_required_fields:{','.join(missing)}")
    category = _clean(row, "category")
    if category not in CATEGORIES:
        raise ValueError(f"invalid_category:{category}")
    project_id = _clean(row, "project_id")
    if not SAFE_ID.fullmatch(project_id):
        raise ValueError("invalid_project_id")
    if project_id != expected_project_id:
        raise IngestionSchemaError(
            f"cross_project_reference:row_{row_index}:{project_id}!={expected_project_id}"
        )
    if not SAFE_ID.fullmatch(_clean(row, "heat_id")):
        raise ValueError("invalid_heat_id")


def _validate_unit(category: str, unit: str) -> None:
    if category == "MEASUREMENT":
        if unit in AMBIGUOUS_UNITS:
            raise ValueError(f"ambiguous_unit:{unit}")
        if unit not in MEASUREMENT_UNITS:
            raise ValueError(f"unknown_unit:{unit}")
    elif unit != NON_MEASUREMENT_UNIT:
        raise ValueError(f"non_measurement_row_must_use_unit_n/a:{unit}")


def validate_and_normalize_row(row: dict, row_index: int, expected_project_id: str) -> NormalizedRow:
    """Raises IngestionSchemaError for whole-batch conditions (cross-project rows);
    raises ValueError for row-scoped schema violations the caller should collect."""
    _validate_common(row, row_index, expected_project_id)
    category = _clean(row, "category")
    unit = _clean(row, "unit")
    _validate_unit(category, unit)
    timestamp = _isoformat_utc(_clean(row, "timestamp"), "timestamp")

    extra: dict = {}
    if category == "OPERATOR_OBSERVATION":
        observer_role = _clean(row, "observer_role")
        validation_plan = _clean(row, "validation_plan")
        if not observer_role:
            raise ValueError("operator_observation_requires_observer_role")
        if not validation_plan:
            raise ValueError("operator_observation_requires_validation_plan")
        occurrence_raw = _clean(row, "occurrence_count") or "1"
        try:
            occurrence_count = int(occurrence_raw)
        except ValueError as exc:
            raise ValueError("invalid_occurrence_count") from exc
        if occurrence_count < 1:
            raise ValueError("invalid_occurrence_count")
        safety_raw = (_clean(row, "safety_critical") or "false").lower()
        if safety_raw not in {"true", "false"}:
            raise ValueError("invalid_safety_critical")
        extra = {
            "observer_role": observer_role, "validation_plan": validation_plan,
            "occurrence_count": occurrence_count, "safety_critical": safety_raw == "true",
            "confidence": _clean(row, "confidence") or DEFAULT_OBSERVATION_CONFIDENCE,
            "operating_context": _clean(row, "operating_context"),
        }
    elif category == "INTERPRETATION":
        extra = {
            "uncertainty": _clean(row, "uncertainty"),
            "applicability_limits": _clean(row, "applicability_limits"),
            "confidence": _clean(row, "confidence") or DEFAULT_INTERPRETATION_CONFIDENCE,
        }
    elif category == "HYPOTHESIS":
        proposed_mechanism = _clean(row, "proposed_mechanism")
        predicted_outcome = _clean(row, "predicted_outcome")
        falsification_test = _clean(row, "falsification_test")
        alternative_hypotheses = _pipe_list(row, "alternative_hypotheses")
        evidence_refs = _pipe_list(row, "evidence_refs")
        experience_refs = _pipe_list(row, "experience_refs")
        if not proposed_mechanism or not predicted_outcome or not falsification_test:
            raise ValueError("hypothesis_missing_required_narrative_field")
        if not alternative_hypotheses:
            raise ValueError("hypothesis_requires_alternatives")
        if not evidence_refs and not experience_refs:
            raise ValueError("hypothesis_requires_grounding")
        for ref in evidence_refs + experience_refs:
            if not SAFE_ID.fullmatch(ref):
                raise ValueError(f"invalid_hypothesis_ref:{ref}")
        extra = {
            "proposed_mechanism": proposed_mechanism, "predicted_outcome": predicted_outcome,
            "falsification_test": falsification_test, "evidence_refs": evidence_refs,
            "experience_refs": experience_refs, "alternative_hypotheses": alternative_hypotheses,
        }

    field_name = _clean(row, "field")
    value = _clean(row, "value")
    statement = _clean(row, "statement")
    record_id = f"{_RECORD_ID_PREFIX[category]}_{_content_hash(project_id=expected_project_id, heat_id=_clean(row, 'heat_id'), category=category, field_name=field_name, value=value, unit=unit, timestamp=timestamp, statement=statement)[:24]}"

    return NormalizedRow(
        row_index=row_index, record_id=record_id, category=category,
        project_id=expected_project_id, heat_id=_clean(row, "heat_id"), field_name=field_name,
        value=value, unit=unit, timestamp=timestamp,
        source_locator=_clean(row, "source_locator"), statement=statement, extra=extra,
    )


def build_record(row: NormalizedRow, domain: str, ingestion_timestamp: str,
                 raw_file_sha256: str):
    locator = _stamp_locator(row.source_locator, ingestion_timestamp, raw_file_sha256)
    title = f"{row.heat_id}:{row.field_name}"
    if row.category == "MEASUREMENT":
        return KnowledgeRecord(
            record_id=row.record_id, record_type="SOURCE", domain=domain, title=title,
            statement=row.statement, source_class="PLANT_MEASUREMENT", source_locator=locator,
            captured_at=row.timestamp, confidence=0.0, project_id=row.project_id,
        )
    if row.category == "OPERATOR_OBSERVATION":
        knowledge = KnowledgeRecord(
            record_id=row.record_id, record_type="EXPERIENCE", domain=domain, title=title,
            statement=row.statement, source_class="OPERATOR_OBSERVATION", source_locator=locator,
            captured_at=row.timestamp, confidence=float(row.extra["confidence"]),
            project_id=row.project_id,
            operating_context=row.extra["operating_context"] or f"heat {row.heat_id}",
        )
        return ExperienceRecord(
            knowledge=knowledge, observer_role=row.extra["observer_role"],
            occurrence_count=row.extra["occurrence_count"], observed_outcome=row.statement,
            validation_plan=row.extra["validation_plan"], safety_critical=row.extra["safety_critical"],
        )
    if row.category == "INTERPRETATION":
        return KnowledgeRecord(
            record_id=row.record_id, record_type="CLAIM", domain=domain, title=title,
            statement=row.statement, source_class="SECONDARY_ANALYSIS", source_locator=locator,
            captured_at=row.timestamp, confidence=float(row.extra["confidence"]),
            project_id=row.project_id, uncertainty=row.extra["uncertainty"],
            applicability_limits=row.extra["applicability_limits"],
        )
    return HypothesisRecord(
        hypothesis_id=row.record_id, domain=domain, problem=row.statement,
        proposed_mechanism=row.extra["proposed_mechanism"],
        predicted_outcome=row.extra["predicted_outcome"],
        falsification_test=row.extra["falsification_test"],
        evidence_refs=row.extra["evidence_refs"], experience_refs=row.extra["experience_refs"],
        alternative_hypotheses=row.extra["alternative_hypotheses"],
        created_at=row.timestamp, project_id=row.project_id,
    )


def _peek_existing_record_ids(store_root: Path) -> set[str]:
    """Read-only scan of events.jsonl. Never creates the store directory, so it is
    safe to call during a dry run against a store that does not exist yet."""
    events_path = store_root / "events.jsonl"
    ids: set[str] = set()
    if not events_path.exists():
        return ids
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        payload = json.loads(line).get("payload", {})
        for key in ("record_id", "hypothesis_id"):
            if key in payload:
                ids.add(payload[key])
        for nested_key in ("knowledge", "record"):
            nested = payload.get(nested_key)
            if isinstance(nested, dict) and "record_id" in nested:
                ids.add(nested["record_id"])
    return ids


def _peek_vault_tamper(store_root: Path, file_sha256: str, suffix: str) -> None:
    """Read-only tamper check. Never creates the raw_evidence directory."""
    path = store_root / "raw_evidence" / f"{file_sha256}{suffix}"
    if not path.exists():
        return
    actual = sha256(path.read_bytes()).hexdigest()
    if actual != file_sha256:
        raise IngestionSchemaError(f"raw_evidence_vault_tampered:{path.name}")


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class IngestionResult:
    status: str  # INGESTED | DRY_RUN
    dry_run: bool
    project_id: str
    source_path: str
    file_sha256: str
    vault_path: str | None
    batch_id: str
    ingestion_timestamp: str
    row_outcomes: tuple[RowOutcome, ...]
    accepted_count: int
    rejected_count: int
    duplicate_count: int
    incomplete_heats: tuple[str, ...]
    event_hashes: tuple[str, ...]
    manifest_path: str | None
    prohibited: tuple[str, ...] = (
        "automatic recipe change", "equipment setpoint recommendation",
        "equipment control", "autonomous promotion of claims",
    )

    def to_json(self) -> dict:
        payload = dict(self.__dict__)
        payload["row_outcomes"] = [outcome.__dict__ for outcome in self.row_outcomes]
        return payload


def _manifest_lock_path(root: Path) -> Path:
    return root / ".ingestion.lock"


def ingest(
    input_path: Path,
    project_id: str,
    store_root: Path,
    *,
    domain: str = "factory_ingestion",
    dry_run: bool = False,
    now: str | None = None,
) -> IngestionResult:
    if not SAFE_ID.fullmatch(project_id):
        raise IngestionSchemaError("invalid_project_id")
    if not input_path.is_file():
        raise IngestionSchemaError(f"input_file_not_found:{input_path}")

    raw_bytes = input_path.read_bytes()
    file_sha256 = sha256(raw_bytes).hexdigest()
    ingestion_timestamp = _isoformat_utc(now or datetime.now(timezone.utc).isoformat(), "ingestion_timestamp")
    batch_id = uuid.uuid4().hex

    store_root = store_root.resolve()
    suffix = input_path.suffix.lower()
    # Read-only checks first; must never create store_root, snapshots/, or raw_evidence/
    # as a side effect of a dry run or of a batch that turns out to be rejected.
    _peek_vault_tamper(store_root, file_sha256, suffix)

    _meta, raw_rows = parse_rows(input_path, raw_bytes)

    normalized_by_index: dict[int, NormalizedRow] = {}
    outcomes: dict[int, RowOutcome] = {}
    for index, row in enumerate(raw_rows):
        try:
            normalized = validate_and_normalize_row(row, index, project_id)
        except IngestionSchemaError:
            raise
        except ValueError as exc:
            outcomes[index] = RowOutcome(index, "REJECTED", row.get("category"), None, str(exc))
            continue
        normalized_by_index[index] = normalized

    existing_ids = _peek_existing_record_ids(store_root)
    seen_in_batch: set[str] = set()
    for index, normalized in list(normalized_by_index.items()):
        if normalized.record_id in existing_ids or normalized.record_id in seen_in_batch:
            outcomes[index] = RowOutcome(index, "DUPLICATE", normalized.category, normalized.record_id,
                                         "duplicate_record")
            del normalized_by_index[index]
            continue
        seen_in_batch.add(normalized.record_id)

    heats: dict[str, list[int]] = {}
    for index, normalized in normalized_by_index.items():
        heats.setdefault(normalized.heat_id, []).append(index)
    incomplete_heats = []
    for heat_id, indices in heats.items():
        has_measurement = any(normalized_by_index[i].category == "MEASUREMENT" for i in indices)
        if not has_measurement:
            incomplete_heats.append(heat_id)
            for index in indices:
                outcomes[index] = RowOutcome(
                    index, "REJECTED", normalized_by_index[index].category,
                    normalized_by_index[index].record_id,
                    "incomplete_heat_record_missing_measurement",
                )
                del normalized_by_index[index]

    for index, normalized in normalized_by_index.items():
        outcomes[index] = RowOutcome(index, "ACCEPTED", normalized.category, normalized.record_id, None)

    ordered_outcomes = tuple(outcomes[i] for i in sorted(outcomes))
    accepted = [normalized_by_index[i] for i in sorted(normalized_by_index)]

    event_hashes: tuple[str, ...] = ()
    vault_path: str | None = None
    manifest_path: str | None = None

    if not dry_run:
        store = ExpertFoundryStore(store_root)
        vault = RawEvidenceVault(store_root / "raw_evidence")
        vault_path = str(vault.store(raw_bytes, file_sha256, suffix))
        written_hashes = []
        for normalized in accepted:
            record = build_record(normalized, domain, ingestion_timestamp, file_sha256)
            written_hashes.append(store.append(record))
        event_hashes = tuple(written_hashes)

        manifest_dir = store_root / "ingestion"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = str(manifest_dir / "manifest.jsonl")
        manifest_lock = _manifest_lock_path(manifest_dir)
        entry = {
            "batch_id": batch_id, "project_id": project_id, "source_path": str(input_path),
            "file_sha256": file_sha256, "ingestion_timestamp": ingestion_timestamp,
            "accepted_count": len(accepted), "rejected_count": sum(1 for o in ordered_outcomes if o.status == "REJECTED"),
            "duplicate_count": sum(1 for o in ordered_outcomes if o.status == "DUPLICATE"),
            "incomplete_heats": incomplete_heats, "event_hashes": list(event_hashes),
        }
        with manifest_lock.open("a+b") as handle:
            _acquire_lock(handle)
            try:
                with open(manifest_path, "a", encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            finally:
                _release_lock(handle)

    return IngestionResult(
        status="DRY_RUN" if dry_run else "INGESTED",
        dry_run=dry_run, project_id=project_id, source_path=str(input_path),
        file_sha256=file_sha256, vault_path=vault_path, batch_id=batch_id,
        ingestion_timestamp=ingestion_timestamp, row_outcomes=ordered_outcomes,
        accepted_count=len(accepted),
        rejected_count=sum(1 for o in ordered_outcomes if o.status == "REJECTED"),
        duplicate_count=sum(1 for o in ordered_outcomes if o.status == "DUPLICATE"),
        incomplete_heats=tuple(incomplete_heats), event_hashes=event_hashes,
        manifest_path=manifest_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Governed factory-data ingestion for the Expert Foundry")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--domain", default="factory_ingestion")
    parser.add_argument("--dry-run", action="store_true",
                         help="Preview what would be ingested without writing anything")
    args = parser.parse_args()
    result = ingest(args.input, args.project_id, args.store, domain=args.domain, dry_run=args.dry_run)
    print(json.dumps(result.to_json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
