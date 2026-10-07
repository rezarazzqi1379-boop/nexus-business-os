from document_completeness_gate import *
def test_title_and_geometry_are_not_controlling_document_set():
 r={"buyer":"BHEL","tender_id":"E5563018","status":"OPEN","product":"bar","geometry":"200mm","material_spec":"AA10119"}
 assert document_state(r)=="DOCUMENT_SET_INCOMPLETE"
def test_complete_set_can_pass():
 r={k:"x" for k in REQUIRED}
 assert document_state(r)=="CONTROLLING_SET_COMPLETE"
