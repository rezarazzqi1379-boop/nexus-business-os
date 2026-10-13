from cross_chat_bootstrap import *
def test_missing_memory_does_not_break_recovery_contract():
 s={k:True for k in REQUIRED}
 assert bootstrap_state(s)=="RECOVERY_READY"
def test_missing_canonical_source_fails_closed():
 s={k:True for k in REQUIRED};s["source_registry"]=False
 assert bootstrap_state(s).startswith("RECOVERY_INCOMPLETE:")
def test_blanket_approval_does_not_unlock_changed_payload():
 assert not protected_action_allowed(exact_approval=True,payload_unchanged=False)
