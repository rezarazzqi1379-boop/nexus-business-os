from steel_trade_hs import assess_alloy_bar_hs

def test_grade_alone_never_assigns_final_hs():
    x=assess_alloy_bar_hs(alloy_steel=True,bar_or_rod=True,condition=None,further_worked=None)
    assert x.candidate_heading=="7228" and x.confidence=="LOW"

def test_forged_candidate_is_722840_not_final_classification():
    x=assess_alloy_bar_hs(alloy_steel=True,bar_or_rod=True,condition="forged",further_worked=False)
    assert x.candidate_heading=="722840"
    assert x.blockers
