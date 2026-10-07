from datetime import date
from pre_rfq_signals import *

def sig(t,**kw):
 d=dict(signal_id=str(t),project_id="PRJ-X",entity_id="E1",signal_type=t,source_locator="src",observed_on=date(2026,10,7),current=True)
 d.update(kw); return PreRFQSignal(**d)

def test_observation_time_is_not_validity_time():
 s=sig(SignalType.CAPEX,valid_from=date(2026,10,8))
 assert not valid_signal(s)

def test_future_procurement_plan_is_valid_pre_rfq_signal():
 s=sig(SignalType.PROCUREMENT_PLAN,valid_from=date(2027,1,1))
 assert valid_signal(s) and pre_rfq_candidate((s,))

def test_historical_award_alone_is_not_pre_rfq_demand():
 s=sig(SignalType.AWARD)
 assert not pre_rfq_candidate((s,))

def test_signal_cluster_scores_more_than_single_weak_signal():
 one=(sig(SignalType.PROCUREMENT_HIRING),)
 cluster=one+(sig(SignalType.PROCUREMENT_PLAN),sig(SignalType.EXPANSION))
 assert cluster_strength(cluster)>cluster_strength(one)
