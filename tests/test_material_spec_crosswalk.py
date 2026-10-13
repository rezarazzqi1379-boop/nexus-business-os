from material_spec_crosswalk import *
def test_structural_steel_family_similarity_is_not_equivalence():
 assert spec_crosswalk(demanded_standard="S275JR",evidenced_standard="S355J2G3",exact_equivalence_source=False)=="NO_EQUIVALENCE_PROVEN"
def test_exact_standard_can_match():
 assert spec_crosswalk(demanded_standard="IS 2062 E250-BR",evidenced_standard="IS 2062 E250-BR",exact_equivalence_source=False)=="EXACT_STANDARD_MATCH"
def test_spec_match_alone_does_not_pass_acceptance():
 assert not acceptance_ready(spec_state="EXACT_STANDARD_MATCH",condition_verified=True,ndt_verified=False,certificate_verified=True)
