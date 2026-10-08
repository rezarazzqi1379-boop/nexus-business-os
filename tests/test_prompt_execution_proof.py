from pathlib import Path
from prompt_evaluator import prompt_ready

def test_recorded_source_roi_execution_proof_contains_contract():
 p=Path(".nexus/cycle_reports/V11_PROMPT_EXECUTION_PROOF_2026-10-07.md").read_text(encoding="utf-8")
 assert prompt_ready(p)
 assert "No production runtime installed" in p
 assert "MERGE_PATTERN" in p and "SANDBOX_PATTERN" in p
