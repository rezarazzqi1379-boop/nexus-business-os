from datetime import date
from pre_rfq_signals import *

def sig(t,**kw):
 d=dict(signal_id=str(t),project_id="PRJ-X",entity_id="E1",signal_type=t,source_locator="src",source_origin="origin-1",observed_on=date(2026,10,7),current=True); d.update(kw); return PreRFQSignal(**d)

def test_observation_time_is_not_validity_time():
 assert not valid_signal(sig(SignalType.CAPEX,valid_from=date(2026,10,8)))
def test_future_procurement_plan_is_valid_pre_rfq_signal():
 s=sig(SignalType.PROCUREMENT_PLAN,valid_from=date(2027,1,1)); assert valid_signal(s) and pre_rfq_candidate((s,))
def test_historical_award_alone_is_not_pre_rfq_demand():
 assert not pre_rfq_candidate((sig(SignalType.AWARD),))
def test_expired_signal_not_current_even_if_flag_true():
 s=sig(SignalType.MAINTENANCE,valid_to=date(2026,10,1)); assert not pre_rfq_candidate((s,),date(2026,10,7))
def test_invalid_validity_interval_rejected():
 assert not valid_signal(sig(SignalType.TENDER,valid_from=date(2026,10,8),valid_to=date(2026,10,1)))
def test_same_origin_does_not_inflate_cluster():
 a=sig(SignalType.PROCUREMENT_HIRING,source_locator="page-a")
 b=sig(SignalType.EXPANSION,source_locator="page-b")
 assert independent_origins((a,b))==1 and cluster_strength((a,b))<=25
def test_independent_cluster_scores_more_than_single_signal():
 one=(sig(SignalType.PROCUREMENT_HIRING),)
 cluster=one+(sig(SignalType.PROCUREMENT_PLAN,source_origin="origin-2"),sig(SignalType.EXPANSION,source_origin="origin-3"))
 assert cluster_strength(cluster)>cluster_strength(one)
