"""Cross-chat bootstrap health contract."""
REQUIRED=("source_registry","project_master","repo_state","ci_state","adapter_policy","dynamic_refresh","project_id")
def bootstrap_state(state:dict)->str:
 missing=tuple(k for k in REQUIRED if not state.get(k))
 return "RECOVERY_READY" if not missing else "RECOVERY_INCOMPLETE:"+",".join(missing)
def protected_action_allowed(*, exact_approval:bool, payload_unchanged:bool)->bool:
 return exact_approval and payload_unchanged
