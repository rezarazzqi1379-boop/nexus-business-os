from pathlib import Path
def test_chain_customer_hunter_v2_preserves_evidence_boundaries():
 p=Path(".nexus/cycle_reports/CHAIN_CUSTOMER_HUNTER_V2_2026-10-07.md").read_text()
 for x in ("EXPIRED/HISTORICAL","PRODUCT DEMAND UNRESOLVED","HISTORICAL BUYING-PATTERN EVIDENCE","EPC-BOUND","industrial-chain demand not yet bound","external action and remains gated","Never invent performance or equivalence"):
  assert x in p
