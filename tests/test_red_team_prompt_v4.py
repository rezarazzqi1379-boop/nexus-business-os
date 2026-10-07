from pathlib import Path

def test_red_team_v4_contract_has_required_guards():
 p=Path(".nexus/prompts/NEXUS_RED_TEAM_MAX_V4.md").read_text()
 required=("SOURCE_REGISTRY","LIVE_CI bound to exact HEAD","FALSE-POSITIVE HUNT","FALSE-NEGATIVE / LOST-OPPORTUNITY HUNT","AUTHORITY × INDEPENDENCE × FRESHNESS × DIRECTNESS","REGRESSION TEST","false_promotion_rate","false_rejection_recovery","REQUIRED VERTICAL PROOF","ACTION BOUNDARY")
 for x in required: assert x in p

def test_red_team_v4_forbids_volume_proxy_and_unguarded_actions():
 p=Path(".nexus/prompts/NEXUS_RED_TEAM_MAX_V4.md").read_text()
 assert "not discovery volume" in p
 assert "Do not send outreach" in p
 assert "Do not add a new agent/tool/database/orchestrator unless" in p
