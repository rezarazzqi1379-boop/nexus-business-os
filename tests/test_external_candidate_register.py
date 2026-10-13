from pathlib import Path

def test_candidate_register_preserves_governed_lifecycle_and_non_actions():
 p=Path(".nexus/registries/EXTERNAL_CAPABILITY_CANDIDATES_V1.md").read_text(encoding="utf-8")
 assert "DISCOVERED -> STUDIED -> SANDBOXED -> ABLATED -> ADMITTED | REJECTED" in p
 assert "No external runtime installed into production" in p
 assert "EXT-OPIK" in p and "EXT-TRACEABLE-RESEARCH" in p

def test_candidate_register_records_authority_contradiction_without_silent_overwrite():
 p=Path(".nexus/registries/EXTERNAL_CAPABILITY_CANDIDATES_V1.md").read_text(encoding="utf-8")
 assert "Preserve the historical text for provenance" in p
 assert "Master v2.1 + Registry v1.8" in p
