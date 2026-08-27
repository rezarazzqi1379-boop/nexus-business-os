from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from canonical_sources import CanonicalStore


def _docx(path: Path, lines: list[str]) -> None:
    paragraphs = "".join(
        f"<w:p><w:r><w:t>{escape(line)}</w:t></w:r></w:p>" for line in lines
    )
    xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>"
        "<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>"
        f"<w:body>{paragraphs}</w:body></w:document>"
    ).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", xml)


class CanonicalAuthorityV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _registry(self, version: str = "1.0") -> Path:
        path = self.root / f"NEXUS_Source_Registry_v{version}.docx"
        _docx(path, [
            f"NEXUS SOURCE REGISTRY v{version}",
            "PRJ-TST-01-ENG",
            "CANONICAL",
            "Test_Master_v2.0.docx",
            "Test engineering authority",
            "No change",
        ])
        return path

    def _project(self, version: str, marker: str) -> Path:
        path = self.root / f"Test_Master_v{version}_{marker}.docx"
        _docx(path, [
            f"TEST ENGINEERING MASTER v{version}",
            "Source ID",
            "PRJ-TST-01-ENG",
            "Project ID",
            "PRJ-TST-01",
            "Version",
            version,
            "Status",
            "CANONICAL",
            marker,
        ])
        return path

    def test_same_source_id_can_preserve_multiple_versions(self):
        store = CanonicalStore(self.root / "canonical.db")
        store.ingest(self._registry())
        store.ingest(self._project("1.0", "historical"))
        store.ingest(self._project("2.0", "active"))
        self.assertEqual(store.status()["count"], 3)
        self.assertEqual(store.latest_for_project("PRJ-TST-01")["version"], "2.0")

    def test_registry_beats_ingest_order_and_newer_unapproved_version(self):
        store = CanonicalStore(self.root / "canonical.db")
        store.ingest(self._registry())
        store.ingest(self._project("2.0", "registry-selected"))
        store.ingest(self._project("3.0", "not-registry-selected"))
        store.ingest(self._project("1.0", "ingested-last"))
        selected = store.latest_for_project("PRJ-TST-01")
        self.assertEqual(selected["version"], "2.0")
        self.assertIn("registry-selected", selected["content"])

    def test_same_source_and_version_with_different_hash_fails_closed(self):
        store = CanonicalStore(self.root / "canonical.db")
        store.ingest(self._registry())
        store.ingest(self._project("2.0", "first"))
        conflict = self._project("2.0", "changed-content")
        with self.assertRaisesRegex(ValueError, "canonical_source_version_collision"):
            store.ingest(conflict)

    def test_legacy_table_is_migrated_additively(self):
        store = CanonicalStore(self.root / "canonical.db")
        store.ingest(self._registry())
        store.ingest(self._project("2.0", "active"))
        reopened = CanonicalStore(self.root / "canonical.db")
        self.assertEqual(reopened.latest_for_project("PRJ-TST-01")["version"], "2.0")


if __name__ == "__main__":
    unittest.main()
