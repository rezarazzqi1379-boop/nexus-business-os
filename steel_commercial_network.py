"""Evidence-bound steel commercial network. Edges are claims, never implied truth."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class NodeType(str,Enum):
 COMPANY="COMPANY"; PLANT="PLANT"; PRODUCT="PRODUCT"; PROCESS="PROCESS"; MATERIAL="MATERIAL"; PROCUREMENT_EVENT="PROCUREMENT_EVENT"; SUPPLIER="SUPPLIER"; ROLE="ROLE"; PERSON="PERSON"; CONTACT="CONTACT"

@dataclass(frozen=True)
class CommercialEdge:
 edge_id:str; project_id:str; source_node:str; target_node:str; relation:str
 source_type:NodeType; target_type:NodeType; source_origin:str; source_locator:str
 observed_at:datetime; authority:str="UNKNOWN"; confidence:float=0.0
 lineage_id:str=""; contradicted:bool=False

def valid_edge(e:CommercialEdge)->bool:
 return bool(e.edge_id and e.project_id and e.source_node and e.target_node and e.relation and e.source_origin and e.source_locator) and 0<=e.confidence<=1

def add_edge(graph:tuple[CommercialEdge,...],e:CommercialEdge)->tuple[CommercialEdge,...]:
 if not valid_edge(e): raise ValueError("invalid_edge")
 if any(x.edge_id==e.edge_id for x in graph): raise ValueError("immutable_edge_id")
 if any(x.project_id!=e.project_id for x in graph): raise ValueError("cross_project_graph")
 return graph+(e,)

def verified_neighbors(graph:tuple[CommercialEdge,...],node:str,min_confidence:float=.7)->tuple[str,...]:
 return tuple(sorted({e.target_node for e in graph if e.source_node==node and not e.contradicted and e.confidence>=min_confidence and e.authority!="UNKNOWN"}))

def relationship_path_ready(graph:tuple[CommercialEdge,...],company:str)->bool:
 relations={e.relation for e in graph if e.source_node==company and not e.contradicted and e.confidence>=.7}
 return "HAS_PROCUREMENT_SIGNAL" in relations and ("HAS_INCUMBENT" in relations or "HAS_RELATIONSHIP_PATH" in relations)
