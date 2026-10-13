from live_tender_gate import *
def test_geometry_does_not_substitute_for_grade():
 assert route_tender(TenderEvidence("RINL",True,"","400x3500"))=="RESOLVE_MATERIAL_SPEC"
def test_closed_same_spec_is_demand_dna_not_current_demand():
 assert route_tender(TenderEvidence("BHEL",False,"AA19331","200x2000-6000"))=="HISTORICAL_DEMAND_DNA"
def test_current_complete_spec_routes_to_technical_review_not_sale():
 x=TenderEvidence("BHEL",True,"AA19331 / IS2004 Class2","200mm","Normalized","UT Category II")
 assert route_tender(x)=="TECHNICAL_REVIEW_READY"
