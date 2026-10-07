from temporal_intelligence import *
from entity_resolution import *
from contradiction_engine import *
from prompt_compiler import *
def test_new_observation_does_not_refresh_expired_fact():
 assert temporal_state(TemporalFact("2025-01-01","2026-10-07",valid_to="2025-12-31"),as_of="2026-10-07")=="EXPIRED"
def test_name_similarity_never_auto_merges():
 assert resolution_state(IdentityEvidence(name_similarity=.99))=="REVIEW_POSSIBLE_ALIAS"
def test_conflict_is_preserved_even_when_authority_resolves_use():
 x=[ClaimValue("79","primary",3,"2026-10-01"),ClaimValue("72","mirror",1,"2026-10-01")]
 assert resolve_values(x)=="AUTHORITY_RESOLVED_WITH_CONTRADICTION"
def test_prompt_compiler_requires_explicit_blocker():
 try: compile_prompt(project_id="STEEL",stage="PRIMARY_DOCUMENT",blocker="",adapters=())
 except ValueError: pass
 else: assert False
