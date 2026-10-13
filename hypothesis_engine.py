"""Hypothesis queue: clues create testable questions, never facts."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Hypothesis:
 statement:str; falsifier:str; required_evidence:str; expected_value:int; cost:int
def priority(h:Hypothesis)->str:
 if not h.statement or not h.falsifier or not h.required_evidence:return "REJECT_UNTESTABLE"
 if h.expected_value<=0:return "DROP_LOW_VALUE"
 return "TEST_NOW" if h.expected_value>h.cost else "BACKLOG"
