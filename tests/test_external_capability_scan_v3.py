from pathlib import Path
def test_external_scan_v3_has_admission_and_safety():
 p=Path(".nexus/cycle_reports/EXTERNAL_CAPABILITY_SCAN_V3_2026-10-07.md").read_text()
 for x in ("SANDBOX BENCHMARK NEXT","zero cross-company false merges","without rerunning expensive agent calls","never treat 2024 historical flow as current demand","do not add a second orchestrator","must not conceal ownership"):
  assert x in p
