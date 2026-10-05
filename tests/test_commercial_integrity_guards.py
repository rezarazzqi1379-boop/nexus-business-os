from commercial_integrity_guards import *

def test_customs_unit_value_is_not_executable_quote():
 a=PriceObservation("bar","42CrMo4","300mm","forged",20,"FOB","USD","t","OFFICIAL_QUOTE")
 b=PriceObservation("bar","42CrMo4","300mm","forged",None,"FOB","USD","t","CUSTOMS_UNIT_VALUE")
 assert price_comparability(a,b)=="NOT_DIRECTLY_COMPARABLE"

def test_cross_standard_similarity_stays_candidate_without_full_evidence():
 assert grade_equivalence(standard_a="EN",standard_b="GOST",chemistry_compared=True,mechanicals_compared=False,heat_treatment_compared=False,delivery_condition_compared=True,mtc_evidence=False)=="CANDIDATE_EQUIVALENCE"

def test_alias_or_possible_subsidiary_needs_resolution():
 assert entity_merge_decision(canonical_domain_same=False,legal_identifier_same=False,alias_only=True,subsidiary_possible=False)=="REQUIRE_RESOLUTION"
 assert entity_merge_decision(canonical_domain_same=True,legal_identifier_same=False,alias_only=False,subsidiary_possible=True)=="REQUIRE_RESOLUTION"
