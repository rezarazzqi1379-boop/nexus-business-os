"""Controlling-document completeness for tender promotion."""
REQUIRED=("buyer","tender_id","status","product","geometry","material_spec","condition","inspection","certificate","eligibility")
def missing_fields(record:dict)->tuple[str,...]:
 return tuple(k for k in REQUIRED if not str(record.get(k,"")).strip())
def document_state(record:dict)->str:
 return "CONTROLLING_SET_COMPLETE" if not missing_fields(record) else "DOCUMENT_SET_INCOMPLETE"
