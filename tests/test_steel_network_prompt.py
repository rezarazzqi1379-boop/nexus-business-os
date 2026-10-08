from pathlib import Path
def test_steel_network_prompt_has_graph_and_safety_contract():
 p=Path(".nexus/prompts/NEXUS_STEEL_NETWORK_DEMAND_HUNTER_V1.md").read_text()
 for x in ("COMPANY → PLANT/SITE","STEEL GENOME","EARLY-DEMAND HUNT","LOST OPPORTUNITY RECOVERY","Authority × Independence × Freshness × Directness","Historical shipment != current demand","Never conceal ownership","time-to-EVIDENCE_READY"):
  assert x in p
