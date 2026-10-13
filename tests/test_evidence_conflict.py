from evidence_conflict import *

def test_conflicting_secondary_values_do_not_majority_resolve():
 xs=(ScalarObservation(5.4,"platform","COMMERCIAL_AGGREGATOR"),ScalarObservation(5.4,"line_items","COMMERCIAL_AGGREGATOR"),ScalarObservation(5.04,"mirror","COMMERCIAL_AGGREGATOR"))
 r=resolve_scalar(xs)
 assert r["state"]=="CONFLICTED" and r["supported_value"] is None

def test_single_primary_value_can_resolve_secondary_conflict():
 xs=(ScalarObservation(5.4,"primary_doc","OFFICIAL_PROCUREMENT",True),ScalarObservation(5.04,"mirror","COMMERCIAL_AGGREGATOR"))
 r=resolve_scalar(xs)
 assert r["state"]=="RESOLVED" and r["supported_value"]==5.4

def test_conflicting_primary_values_remain_conflicted():
 xs=(ScalarObservation(5.4,"p1","OFFICIAL_PROCUREMENT",True),ScalarObservation(5.04,"p2","OFFICIAL_PROCUREMENT",True))
 assert resolve_scalar(xs)["state"]=="CONFLICTED"
