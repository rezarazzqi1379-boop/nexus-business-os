from intelligence_graph import *
from thread_linker import *
from hypothesis_engine import *
def n(i,p="STEEL"): return Node(i,"x",p,"2026-10-07","src","FACT")
def test_cross_project_links_blocked():
 try: link(n("a","A"),n("b","B"),"x","src")
 except ValueError as e: assert str(e)=="cross_project_link_blocked"
 else: assert False
def test_unverified_link_never_promotes():
 assert not promotion_allowed(link(n("a"),n("b"),"possible_supplier","src"))
def test_multiple_independent_clues_route_verification_not_truth():
 s=thread_score(same_buyer=True,same_spec=True,same_geometry=True,independent_source=True)
 assert route_thread(s)=="HIGH_PRIORITY_VERIFY"
def test_untestable_hypothesis_rejected():
 assert priority(Hypothesis("buyer may recur","","primary award",10,1))=="REJECT_UNTESTABLE"
