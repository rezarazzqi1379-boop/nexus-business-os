"""Eligibility is a separate commercial gate; an open tender is not bidder eligibility."""
def eligibility_state(*, tender_open:bool, registration_verified:bool, pqr_verified:bool, origin_ok:bool, financial_ok:bool)->str:
 if not tender_open:return "NOT_CURRENT"
 if not registration_verified:return "REGISTRATION_UNKNOWN"
 if not pqr_verified:return "PQR_UNKNOWN"
 if not origin_ok:return "ORIGIN_OR_LOCAL_CONTENT_REVIEW"
 if not financial_ok:return "FINANCIAL_QUALIFICATION_REVIEW"
 return "ELIGIBILITY_EVIDENCED"
