"""Route adapters by evidence task; tools never become authority by connection alone."""
ROUTES={
 "canonical_recovery":"FILES",
 "code_ci":"GITHUB",
 "live_discovery":"EXA_SEARCH",
 "operational_state":"NOTION",
 "durable_evidence":"GOOGLE_DRIVE",
 "crm_read":"HUBSPOT",
 "trade_discovery":"ABRAMS",
 "decision_person":"LINKEDIN",
}
def route(task:str)->str:return ROUTES.get(task,"NO_ADAPTER_JUSTIFIED")
def can_auto_use(adapter:str, *, paid:bool=False, external_write:bool=False)->bool:
 if paid or external_write:return False
 return adapter in {"FILES","GITHUB","EXA_SEARCH","NOTION","GOOGLE_DRIVE","HUBSPOT","ABRAMS","LINKEDIN"}
