from steel_customs_record import CustomsRecord,validate_customs_record
def test_candidate_can_remain_nonfinal():
 r=CustomsRecord("EAEU","722840","bar","forged",False,("source:tariff",))
 assert validate_customs_record(r)==()
def test_final_needs_authority():
 r=CustomsRecord("EAEU","722840","bar","forged",False,("source:tariff",),final=True)
 assert "final_requires_review_authority" in validate_customs_record(r)
