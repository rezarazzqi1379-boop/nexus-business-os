import hashlib
from dataclasses import dataclass
from enum import Enum

class ReadOnlyViolation(RuntimeError): pass
class State(str,Enum): FOUND="FOUND"; NOT_FOUND="NOT_FOUND"; UNKNOWN="UNKNOWN"
@dataclass
class Result: state:State; provider_message_id:str|None=None; evidence:str|None=None

def deterministic_message_id(operation_key:str)->str:
    d=hashlib.sha256(operation_key.encode()).hexdigest()[:32]
    return f"<nexus-{d}@nexus.local>"

class GmailReadOnly:
    def __init__(self,search_ids): self.search_ids=search_ids
    def find_sent(self,message_id:str)->Result:
        try:
            ids=self.search_ids(f"in:sent rfc822msgid:{message_id}",5)
            return Result(State.FOUND,ids[0]) if ids else Result(State.NOT_FOUND,evidence="no match")
        except Exception as e: return Result(State.UNKNOWN,evidence=type(e).__name__)
    def send(self,*a,**k): raise ReadOnlyViolation("Gmail write disabled")
    create_draft=send; modify=send
