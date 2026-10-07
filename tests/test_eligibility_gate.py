from eligibility_gate import *
def test_open_tender_does_not_prove_registration():
 assert eligibility_state(tender_open=True,registration_verified=False,pqr_verified=True,origin_ok=True,financial_ok=True)=="REGISTRATION_UNKNOWN"
def test_all_eligibility_layers_required():
 assert eligibility_state(tender_open=True,registration_verified=True,pqr_verified=True,origin_ok=True,financial_ok=True)=="ELIGIBILITY_EVIDENCED"
