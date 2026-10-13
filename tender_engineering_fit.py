"""Engineering-fit gate for tender-to-capability decisions."""
def engineering_fit(*, geometry_capable:bool, controlling_spec_verified:bool, condition_verified:bool, ndt_verified:bool, current_stock_verified:bool)->str:
 if not geometry_capable:return "NO_GEOMETRY_FIT"
 if not controlling_spec_verified:return "ENGINEERING_REVIEW_SPEC"
 if not condition_verified:return "ENGINEERING_REVIEW_CONDITION"
 if not ndt_verified:return "ENGINEERING_REVIEW_NDT"
 if not current_stock_verified:return "TECHNICAL_FIT_STOCK_UNCONFIRMED"
 return "TECHNICAL_AND_STOCK_FIT"
