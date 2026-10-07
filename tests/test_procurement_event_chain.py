from datetime import datetime,timezone
import pytest
from procurement_event_chain import *

T=datetime(2026,1,1,tzinfo=timezone.utc)
def e(**kw):
 d=dict(process_id="P",event_id="E1",project_id="NEXUS-BUSINESS-OS",buyer_id="B",stage=ProcurementStage.PLANNING,source_locator="official:1",observed_at=T,event_at=T); d.update(kw); return ProcurementEvent(**d)

def test_events_are_append_only_and_id_unique():
 h=append_event((),e())
 with pytest.raises(ValueError): append_event(h,e())
def test_supersession_requires_existing_same_process_event():
 with pytest.raises(ValueError): append_event((),e(event_id="E2",supersedes_event_id="E1"))
def test_stage_chain_preserves_history_not_latest_snapshot_only():
 h=append_event((),e())
 h=append_event(h,e(event_id="E2",stage=ProcurementStage.TENDER,event_at=datetime(2026,2,1,tzinfo=timezone.utc),supersedes_event_id="E1"))
 assert stage_progression(h,"P")== (ProcurementStage.PLANNING,ProcurementStage.TENDER)
def test_supplier_change_detected_across_awards_contracts():
 h=append_event((),e(stage=ProcurementStage.AWARD,supplier_id="S1"))
 h=append_event(h,e(event_id="E2",stage=ProcurementStage.CONTRACT,supplier_id="S2"))
 assert supplier_change(h,"P")
def test_process_cannot_cross_project_boundary():
 h=append_event((),e())
 with pytest.raises(ValueError): append_event(h,e(event_id="E2",project_id="PRJ-HYD-01"))


def test_invalid_validity_window_rejected():
 with pytest.raises(ValueError):
  append_event((),e(valid_from=datetime(2026,2,1,tzinfo=timezone.utc),valid_to=T))

def test_expired_or_noncurrent_event_not_current():
 old=e(valid_from=T,valid_to=datetime(2026,1,31,tzinfo=timezone.utc))
 assert not current_events((old,),"P",datetime(2026,2,1,tzinfo=timezone.utc))
 assert not current_events((e(current=False),),"P",T)

def test_superseded_event_drops_from_current_view():
 h=append_event((),e())
 h=append_event(h,e(event_id="E2",stage=ProcurementStage.TENDER,supersedes_event_id="E1"))
 assert tuple(x.event_id for x in current_events(h,"P",T))==("E2",)

def test_bidder_is_not_incumbent():
 h=(e(stage=ProcurementStage.AWARD,supplier_id="S1",bidder_ids=("S1",),award_state=AwardState.BIDDER_ONLY),)
 assert incumbent_supplier(h,"P")==""

def test_hidden_winner_is_not_incumbent():
 h=(e(stage=ProcurementStage.AWARD,award_state=AwardState.WINNER_HIDDEN),)
 assert incumbent_supplier(h,"P")==""

def test_verified_winner_can_be_incumbent():
 h=(e(stage=ProcurementStage.AWARD,supplier_id="S1",award_state=AwardState.WINNER_VERIFIED),)
 assert incumbent_supplier(h,"P")=="S1"
 assert verified_winners(h,"P")==("S1",)

def test_supplier_change_requires_verified_winners():
 h=(e(stage=ProcurementStage.AWARD,supplier_id="S1",award_state=AwardState.BIDDER_ONLY),
    e(event_id="E2",stage=ProcurementStage.AWARD,supplier_id="S2",award_state=AwardState.BIDDER_ONLY))
 assert not supplier_change(h,"P")
