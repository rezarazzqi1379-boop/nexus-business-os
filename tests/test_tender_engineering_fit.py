from tender_engineering_fit import *
def test_geometry_alone_never_proves_technical_fit():
 assert engineering_fit(geometry_capable=True,controlling_spec_verified=False,condition_verified=True,ndt_verified=True,current_stock_verified=True)=="ENGINEERING_REVIEW_SPEC"
def test_exact_technical_fit_without_fresh_stock_stays_stock_unconfirmed():
 assert engineering_fit(geometry_capable=True,controlling_spec_verified=True,condition_verified=True,ndt_verified=True,current_stock_verified=False)=="TECHNICAL_FIT_STOCK_UNCONFIRMED"
def test_all_layers_required():
 assert engineering_fit(geometry_capable=True,controlling_spec_verified=True,condition_verified=True,ndt_verified=True,current_stock_verified=True)=="TECHNICAL_AND_STOCK_FIT"
