from pathlib import Path

def test_census_counts_all_historical_v10_cycle_prompts():
    paths=list(Path(".nexus/prompts").glob("NEXUS_CONTINUE_V10*.md"))
    census=Path(".nexus/prompts/NEXUS_PROMPT_CENSUS_V1.md").read_text()
    assert len(paths)==25
    assert "HISTORICAL_CYCLE_PROMPT" in census

def test_archived_prompt_cannot_become_authority():
    census=Path(".nexus/prompts/NEXUS_PROMPT_CENSUS_V1.md").read_text()
    assert "not simultaneously active system instructions" in census
    assert "Do not automatically concatenate V10 prompts" in census
    assert "Source Registry, project master or action gate" in census

def test_retirement_is_reversible():
    census=Path(".nexus/prompts/NEXUS_PROMPT_CENSUS_V1.md").read_text()
    assert "No historical file is deleted or modified" in census
    assert "measurable acceptance test" in census

def test_active_stack_preserves_canonical_authority():
    census=Path(".nexus/prompts/NEXUS_PROMPT_CENSUS_V1.md").read_text()
    for x in ("Canonical Source Registry + project master","Operator v3","NEXUS_PROMPT_OS_REGISTRY_V2.md"):
        assert x in census
