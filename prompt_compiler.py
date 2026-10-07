"""Compile minimal execution context from stable kernel and measured stage."""
def compile_prompt(*,project_id:str,stage:str,blocker:str,adapters:tuple[str,...])->str:
 if not project_id or not stage or not blocker: raise ValueError("incomplete_execution_context")
 a=", ".join(adapters) if adapters else "NONE"
 return f"LOAD NEXUS_GLOBAL_KERNEL_V1.\nPROJECT={project_id}\nSTAGE={stage}\nBLOCKER={blocker}\nALLOWED_ADAPTERS={a}\nRecover live state; execute only this stage; preserve provenance/project isolation; test, measure, persist, and stop at protected gates."
