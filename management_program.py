"""NEXUS management program: evidence-bound mission portfolio and WIP control."""
from dataclasses import dataclass
from enum import Enum

class MissionState(str,Enum):
 INTAKE="INTAKE"; ACTIVE="ACTIVE"; VERIFY="VERIFY"; BLOCKED="BLOCKED"; GATED="GATED"; DONE="DONE"; PARKED="PARKED"

@dataclass(frozen=True)
class Mission:
 mission_id:str; project_id:str; objective:str; bottleneck:str; acceptance_test:str
 metric_name:str; baseline:float; target:float; owner_role:str
 evidence_refs:tuple[str,...]; next_safe_action:str
 dependencies:tuple[str,...]=(); critical_unknowns:tuple[str,...]=()
 protected_action:bool=False; contradiction:bool=False; completed:bool=False

def valid(m:Mission)->bool:
 return all((m.mission_id,m.project_id,m.objective,m.bottleneck,m.acceptance_test,m.metric_name,m.owner_role,m.next_safe_action)) and m.target!=m.baseline

def mission_state(m:Mission)->MissionState:
 if not valid(m):return MissionState.INTAKE
 if m.contradiction:return MissionState.BLOCKED
 if m.protected_action:return MissionState.GATED
 if m.completed:return MissionState.DONE
 if m.critical_unknowns:return MissionState.VERIFY
 return MissionState.ACTIVE

def admit_active(m:Mission)->bool:
 return mission_state(m)==MissionState.ACTIVE and bool(m.evidence_refs)

def portfolio(missions:tuple[Mission,...],wip_limit:int=3)->tuple[Mission,...]:
 if wip_limit<1:raise ValueError("invalid_wip_limit")
 ids=[m.mission_id for m in missions]
 if len(ids)!=len(set(ids)):raise ValueError("duplicate_mission")
 active=[m for m in missions if admit_active(m)]
 return tuple(active[:wip_limit])

def may_close(m:Mission,measured_value:float,test_green:bool)->bool:
 if not test_green or m.contradiction or m.protected_action:return False
 if m.target>m.baseline:return measured_value>=m.target
 return measured_value<=m.target

def management_snapshot(missions:tuple[Mission,...],wip_limit:int=3)->dict:
 return {
  "active":tuple(m.mission_id for m in portfolio(missions,wip_limit)),
  "verify":tuple(m.mission_id for m in missions if mission_state(m)==MissionState.VERIFY),
  "blocked":tuple(m.mission_id for m in missions if mission_state(m)==MissionState.BLOCKED),
  "gated":tuple(m.mission_id for m in missions if mission_state(m)==MissionState.GATED),
  "done":tuple(m.mission_id for m in missions if mission_state(m)==MissionState.DONE),
 }
