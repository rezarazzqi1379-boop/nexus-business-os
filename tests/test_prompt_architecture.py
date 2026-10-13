from pathlib import Path
def test_global_kernel_has_required_governance_sections():
 t=Path(".nexus/prompts/NEXUS_GLOBAL_KERNEL_V1.md").read_text()
 for x in ["SESSION BOOT","EVIDENCE","INTELLIGENCE","ADAPTER FABRIC","PROTECTED ACTIONS","COMMERCIAL CONVERSION","LEARNING","SESSION CLOSE"]: assert x in t
def test_stage_map_covers_recovery_to_action_gate():
 t=Path(".nexus/prompts/NEXUS_STAGED_PROMPT_MAP_V1.md").read_text()
 assert "S0 RECOVERY" in t and "S15 ACTION GATE" in t and "S11 RED TEAM" in t
