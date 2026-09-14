from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from hashlib import sha256
from pathlib import Path
from xml.sax.saxutils import escape

from expert_foundry import ExpertFoundryStore
from foundry_ingestion import IngestionSchemaError, ingest


NOW = "2026-09-08T00:00:00+00:00"
LATER = "2026-09-08T01:00:00+00:00"

CSV_HEADER = "project_id,heat_id,category,field,value,unit,timestamp,source_locator,statement"


def _measurement_row(project="steel_ingot_pilot", heat="heat_001", field="tap_temperature",
                      value="1550", unit="degC", ts=NOW, locator="row:2",
                      statement="tap temperature reading"):
    return f"{project},{heat},MEASUREMENT,{field},{value},{unit},{ts},{locator},{statement}"


def _write_csv(path: Path, lines: list[str]) -> None:
    path.write_text(CSV_HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def _index_to_col_letters(index: int) -> str:
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def build_minimal_xlsx(headers: list[str], rows: list[list[str]]) -> bytes:
    """Hand-built minimal OOXML package (no openpyxl dependency available)."""
    all_rows = [headers] + rows
    shared: list[str] = []
    shared_index: dict[str, int] = {}

    def shared_str_index(text: str) -> int:
        if text not in shared_index:
            shared_index[text] = len(shared)
            shared.append(text)
        return shared_index[text]

    sheet_rows_xml = []
    for r, row in enumerate(all_rows, start=1):
        cells_xml = []
        for c, value in enumerate(row):
            col_letter = _index_to_col_letters(c)
            idx = shared_str_index(str(value))
            cells_xml.append(f'<c r="{col_letter}{r}" t="s"><v>{idx}</v></c>')
        sheet_rows_xml.append(f'<row r="{r}">' + "".join(cells_xml) + "</row>")

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>" + "".join(sheet_rows_xml) + "</sheetData></worksheet>"
    )
    shared_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(shared)}" uniqueCount="{len(shared)}">'
        + "".join(f"<si><t>{escape(s)}</t></si>" for s in shared)
        + "</sst>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
        'Target="sharedStrings.xml"/>'
        "</Relationships>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        archive.writestr("xl/sharedStrings.xml", shared_xml)
    return buffer.getvalue()


class CsvIngestionTests(unittest.TestCase):
    def test_valid_measurement_is_accepted_and_appended(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.status, "INGESTED")
            events = (temp / "store" / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn(f"raw_sha256={result.file_sha256}", events)
            self.assertIn('"confidence":0.0', events)
            self.assertEqual(result.accepted_count, 1)
            self.assertEqual(result.rejected_count, 0)
            self.assertEqual(len(result.event_hashes), 1)
            store = ExpertFoundryStore(temp / "store")
            self.assertTrue(store.verify_chain())

    def test_missing_unit_is_rejected_not_written(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row(unit="")])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 0)
            self.assertEqual(result.rejected_count, 1)
            self.assertIn("missing_required_fields", result.row_outcomes[0].reason)

    def test_ambiguous_unit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row(unit="deg")])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 0)
            self.assertIn("ambiguous_unit", result.row_outcomes[0].reason)

    def test_unknown_unit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row(unit="parsecs")])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertIn("unknown_unit", result.row_outcomes[0].reason)

    def test_non_measurement_row_must_use_unit_placeholder(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [
                _measurement_row(),
                "steel_ingot_pilot,heat_001,INTERPRETATION,tap_temperature,within_range,degC,"
                f"{NOW},row:3,temperature looks nominal",
            ])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            interpretation_outcome = result.row_outcomes[1]
            self.assertEqual(interpretation_outcome.status, "REJECTED")
            self.assertIn("non_measurement_row_must_use_unit_n/a", interpretation_outcome.reason)

    def test_malformed_csv_missing_header_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            input_path.write_bytes(b"")
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)

    def test_cross_project_row_aborts_whole_batch_with_no_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [
                _measurement_row(project="steel_ingot_pilot"),
                _measurement_row(project="other_project", field="tap_temperature2"),
            ])
            store_root = temp / "store"
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", store_root, now=LATER)
            self.assertFalse((store_root / "events.jsonl").exists())
            self.assertFalse((store_root / "raw_evidence").exists() and
                              any((store_root / "raw_evidence").iterdir()))

    def test_heat_with_measurement_is_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row(heat="heat_001")])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 1)
            self.assertEqual(result.incomplete_heats, ())

    def test_duplicate_row_within_batch_is_flagged_and_not_double_written(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row(), _measurement_row()])
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 1)
            self.assertEqual(result.duplicate_count, 1)
            self.assertEqual(result.row_outcomes[1].status, "DUPLICATE")

    def test_duplicate_across_separate_ingestion_runs_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            store_root = temp / "store"
            first = ingest(input_path, "steel_ingot_pilot", store_root, now=NOW)
            second = ingest(input_path, "steel_ingot_pilot", store_root, now=LATER)
            self.assertEqual(first.accepted_count, 1)
            self.assertEqual(second.accepted_count, 0)
            self.assertEqual(second.duplicate_count, 1)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            store_root = temp / "store"
            result = ingest(input_path, "steel_ingot_pilot", store_root, dry_run=True, now=NOW)
            self.assertEqual(result.status, "DRY_RUN")
            self.assertEqual(result.accepted_count, 1)
            self.assertEqual(result.event_hashes, ())
            self.assertFalse((store_root / "events.jsonl").exists())
            self.assertFalse((store_root / "raw_evidence").exists())
            self.assertFalse((store_root / "ingestion").exists())

    def test_original_file_is_never_modified(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            before = input_path.read_bytes()
            before_hash = sha256(before).hexdigest()
            ingest(input_path, "steel_ingot_pilot", temp / "store", now=NOW)
            after = input_path.read_bytes()
            self.assertEqual(before, after)
            self.assertEqual(sha256(after).hexdigest(), before_hash)

    def test_vaulted_copy_is_byte_identical_to_original(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            original_bytes = input_path.read_bytes()
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=NOW)
            self.assertEqual(Path(result.vault_path).read_bytes(), original_bytes)

    def test_tampered_vault_is_detected_and_blocks_reingestion(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.csv"
            _write_csv(input_path, [_measurement_row()])
            store_root = temp / "store"
            first = ingest(input_path, "steel_ingot_pilot", store_root, now=NOW)
            vault_path = Path(first.vault_path)
            vault_path.chmod(0o600)
            vault_path.write_bytes(b"tampered evidence bytes")
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", store_root, now=LATER)


class JsonIngestionTests(unittest.TestCase):
    def test_json_row_list_is_ingested(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.json"
            input_path.write_text(json.dumps([
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_010",
                    "category": "MEASUREMENT", "field": "tap_temperature", "value": 1550,
                    "unit": "degC", "timestamp": NOW, "source_locator": "cell:B2",
                    "statement": "tap temperature reading",
                },
            ]), encoding="utf-8")
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 1)

    def test_malformed_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.json"
            input_path.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)

    def test_hypothesis_row_requires_grounding_and_alternatives(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.json"
            input_path.write_text(json.dumps([
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_020",
                    "category": "MEASUREMENT", "field": "tap_temperature", "value": "1550",
                    "unit": "degC", "timestamp": NOW, "source_locator": "cell:B2",
                    "statement": "tap temperature reading",
                },
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_020",
                    "category": "HYPOTHESIS", "field": "porosity", "value": "n/a",
                    "unit": "n/a", "timestamp": NOW, "source_locator": "cell:B3",
                    "statement": "Porosity may correlate with tap temperature",
                    "proposed_mechanism": "Lower tap temperature increases gas entrapment",
                    "predicted_outcome": "Heats with lower tap temperature show more porosity",
                    "falsification_test": "Compare porosity across a temperature-matched heat pair",
                    "alternative_hypotheses": "Porosity is dominated by mould coating instead",
                    "evidence_refs": "",
                    "experience_refs": "",
                },
            ]), encoding="utf-8")
            # hypothesis row provides no evidence/experience refs -> must be rejected
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            hypothesis_outcome = result.row_outcomes[1]
            self.assertEqual(hypothesis_outcome.status, "REJECTED")
            self.assertIn("hypothesis_requires_grounding", hypothesis_outcome.reason)

    def test_heat_without_any_measurement_row_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.json"
            input_path.write_text(json.dumps([
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_050",
                    "category": "OPERATOR_OBSERVATION", "field": "slag_appearance",
                    "value": "glassy", "unit": "n/a", "timestamp": NOW, "source_locator": "cell:B2",
                    "statement": "operator observed glassy slag surface",
                    "observer_role": "melter", "validation_plan": "compare next three heats",
                },
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_050",
                    "category": "INTERPRETATION", "field": "slag_appearance",
                    "value": "normal", "unit": "n/a", "timestamp": NOW, "source_locator": "cell:B3",
                    "statement": "slag appearance looks within normal range",
                },
            ]), encoding="utf-8")
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 0)
            self.assertEqual(result.incomplete_heats, ("heat_050",))
            self.assertTrue(all(
                outcome.status == "REJECTED" and
                outcome.reason == "incomplete_heat_record_missing_measurement"
                for outcome in result.row_outcomes
            ))

    def test_operator_observation_ingests_as_experience_record(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.json"
            input_path.write_text(json.dumps([
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_030",
                    "category": "MEASUREMENT", "field": "tap_temperature", "value": "1550",
                    "unit": "degC", "timestamp": NOW, "source_locator": "cell:B2",
                    "statement": "tap temperature reading",
                },
                {
                    "project_id": "steel_ingot_pilot", "heat_id": "heat_030",
                    "category": "OPERATOR_OBSERVATION", "field": "slag_appearance",
                    "value": "glassy", "unit": "n/a", "timestamp": NOW, "source_locator": "cell:B3",
                    "statement": "operator observed glassy slag surface",
                    "observer_role": "melter", "validation_plan": "compare next three heats",
                    "occurrence_count": "2", "safety_critical": "false",
                },
            ]), encoding="utf-8")
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 2)
            store_events = (temp / "store" / "events.jsonl").read_text()
            self.assertIn("validation_plan", store_events)
            self.assertIn("EXPERIENCE", store_events)


class XlsxIngestionTests(unittest.TestCase):
    def test_xlsx_measurement_row_is_ingested(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.xlsx"
            headers = ["project_id", "heat_id", "category", "field", "value", "unit",
                       "timestamp", "source_locator", "statement"]
            rows = [["steel_ingot_pilot", "heat_040", "MEASUREMENT", "tap_temperature", "1550",
                     "degC", NOW, "sheet1!B2", "tap temperature reading"]]
            input_path.write_bytes(build_minimal_xlsx(headers, rows))
            result = ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)
            self.assertEqual(result.accepted_count, 1)
            self.assertEqual(result.rejected_count, 0)

    def test_malformed_xlsx_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.xlsx"
            input_path.write_bytes(b"not a real zip file")
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)


class UnsupportedFormatTests(unittest.TestCase):
    def test_unsupported_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            input_path = temp / "heat.txt"
            input_path.write_text("irrelevant", encoding="utf-8")
            with self.assertRaises(IngestionSchemaError):
                ingest(input_path, "steel_ingot_pilot", temp / "store", now=LATER)


if __name__ == "__main__":
    unittest.main()
