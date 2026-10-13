import discovery_coverage as m

def covered():
 return {x:"COVERED" for x in m.REQUIRED_MARKET_LAYERS}

def test_complete_requires_every_required_layer():
 s=covered();del s["TRADER"]
 r=m.evaluate_market_coverage(s)
 assert not r["complete"] and "TRADER" in r["missing"]

def test_unsearched_stockist_blocks_completion():
 s=covered();s["STOCKIST"]="NOT_SEARCHED"
 r=m.evaluate_market_coverage(s)
 assert not r["complete"] and "STOCKIST" in r["blind"]

def test_provider_failure_is_blind_not_negative_evidence():
 s=covered();s["IMPORTER"]="SOURCE_UNAVAILABLE"
 r=m.evaluate_market_coverage(s)
 assert not r["complete"] and "IMPORTER" in r["blind"]

def test_documented_no_evidence_counts_as_checked():
 s=covered();s["TRADER"]="NO_EVIDENCE"
 assert m.can_mark_market_discovery_complete(s)

def test_negative_evidence_is_distinct_state():
 s=covered();s["TRADER"]="NEGATIVE_EVIDENCE"
 assert m.evaluate_market_coverage(s)["complete"]
 assert s["TRADER"]!="NO_EVIDENCE"

def test_manufacturer_alone_never_completes_market():
 s={"MANUFACTURER":"COVERED"}
 assert not m.can_mark_market_discovery_complete(s)

def test_invalid_state_fails_closed():
 s=covered();s["END_USER"]="FOUND"
 r=m.evaluate_market_coverage(s)
 assert not r["complete"] and r["invalid"]=={"END_USER":"FOUND"}
