from enum import Enum
class Decision(str,Enum): ACK="ACK_ALREADY_EXECUTED"; HOLD="HOLD_UNCERTAIN"; RETRY="SAFE_TO_RETRY"
def decide(found:bool|None,strong_idempotency=False,strong_negative_lookup=False):
    if found is True: return Decision.ACK
    if found is None: return Decision.HOLD
    if strong_idempotency and strong_negative_lookup: return Decision.RETRY
    return Decision.HOLD
