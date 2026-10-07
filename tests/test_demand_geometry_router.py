from demand_geometry_router import *
def test_small_same_grade_rejected_before_qualification():
 d=DemandGeometry("42CrMo4","round",250,5)
 assert geometry_route(d,stock_grade="42CrMo4",stock_form="round",dmin=290,dmax=760,lmin=2,lmax=7)=="REJECT_DIAMETER"
def test_missing_size_goes_to_followup():
 d=DemandGeometry("42CrMo4","round",None,None)
 assert geometry_route(d,stock_grade="42CrMo4",stock_form="round",dmin=290,dmax=760,lmin=2,lmax=7)=="FOLLOWUP_MISSING_GEOMETRY"
