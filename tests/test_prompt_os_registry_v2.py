from pathlib import Path

def test_prompt_os_v2_declares_authority_and_supersession():
 t=Path(".nexus/prompts/NEXUS_PROMPT_OS_REGISTRY_V2.md").read_text()
 assert "Supersedes: NEXUS Prompt OS Registry v1" in t
 assert "Source Registry + canonical project master remain above" in t

def test_prompt_os_v2_replaces_generic_procurement_route():
 t=Path(".nexus/prompts/NEXUS_PROMPT_OS_REGISTRY_V2.md").read_text()
 assert "GENERIC_WEB_PROCUREMENT → replace with DIRECT_PROCUREMENT_AWARD" in t
 assert "APPLICATION_FIRST" in t and "SUPPORT_ONLY" in t

def test_prompt_os_v2_preserves_award_semantics():
 t=Path(".nexus/prompts/NEXUS_PROMPT_OS_REGISTRY_V2.md").read_text()
 for x in ("Bidder ≠ winner","hidden winner ≠ verified incumbent","supplier change requires verified winners"):
  assert x in t

def test_prompt_os_v2_has_reversible_lifecycle():
 t=Path(".nexus/prompts/NEXUS_PROMPT_OS_REGISTRY_V2.md").read_text()
 assert "DRAFT → IMPLEMENTED → TESTED → ACTIVE → DEPRECATED → SUPERSEDED" in t
 assert "rollback_target" in t
