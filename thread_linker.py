"""Thread-link scoring for discovery. Scores route review; they do not establish truth."""
def thread_score(*,same_buyer=False,same_spec=False,same_geometry=False,same_document=False,same_time_window=False,independent_source=False)->int:
 return sum((2 if same_buyer else 0,3 if same_spec else 0,2 if same_geometry else 0,4 if same_document else 0,1 if same_time_window else 0,2 if independent_source else 0))
def route_thread(score:int)->str:
 if score>=9:return "HIGH_PRIORITY_VERIFY"
 if score>=5:return "REVIEW_LINK"
 return "WEAK_THREAD"
