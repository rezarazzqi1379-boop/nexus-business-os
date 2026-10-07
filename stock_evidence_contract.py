"""Stock evidence completeness contract for auditable availability."""
REQUIRED=("observed_at","grade","standard","diameter","length","tonnage","condition","heat_lot","certificate_ref","availability_window","source_owner")
def missing_stock_fields(record:dict)->tuple[str,...]:
 return tuple(k for k in REQUIRED if not str(record.get(k,"")).strip())
def stock_evidence_state(record:dict)->str:
 return "CURRENT_STOCK_EVIDENCED" if not missing_stock_fields(record) else "INCOMPLETE_STOCK_EVIDENCE"
