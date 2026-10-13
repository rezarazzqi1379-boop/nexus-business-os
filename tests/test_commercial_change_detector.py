from datetime import datetime,timezone
import pytest
from procurement_event_chain import ProcurementEvent,ProcurementStage,ChangeType as EventChangeType,AwardState
from commercial_change_detector import detect_change,ChangeType
T=datetime(2026,1,1,tzinfo=timezone.utc)
def e(**kw):
 d=dict(process_id="P",event_id="E1",project_id="NEXUS-BUSINESS-OS",buyer_id="B",stage=ProcurementStage.PLANNING,source_locator="u",observed_at=T,event_at=T); d.update(kw); return ProcurementEvent(**d)

def test_tender_stage_advance_is_review_signal_not_action_authority():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.change_type==ChangeType.STAGE_ADVANCE and c.commercial_review_signal

def test_supplier_change_requires_two_verified_winners():
 c=detect_change(
  e(stage=ProcurementStage.AWARD,supplier_id="A",award_state=AwardState.WINNER_VERIFIED),
  e(event_id="E2",stage=ProcurementStage.CONTRACT,supplier_id="B",award_state=AwardState.WINNER_VERIFIED))
 assert c.change_type==ChangeType.SUPPLIER_CHANGE and c.commercial_review_signal

def test_bidder_or_supplier_mentions_do_not_create_supplier_change():
 c=detect_change(
  e(stage=ProcurementStage.AWARD,supplier_id="A",award_state=AwardState.BIDDER_ONLY),
  e(event_id="E2",stage=ProcurementStage.CONTRACT,supplier_id="B",award_state=AwardState.BIDDER_ONLY))
 assert c.change_type!=ChangeType.SUPPLIER_CHANGE

def test_hidden_winner_does_not_create_incumbent_change():
 c=detect_change(
  e(stage=ProcurementStage.AWARD,supplier_id="A",award_state=AwardState.WINNER_HIDDEN),
  e(event_id="E2",stage=ProcurementStage.CONTRACT,supplier_id="B",award_state=AwardState.WINNER_HIDDEN))
 assert c.change_type!=ChangeType.SUPPLIER_CHANGE

def test_typed_spec_change_is_preserved_and_reviewed():
 c=detect_change(e(stage=ProcurementStage.TENDER),e(event_id="E2",stage=ProcurementStage.TENDER,change_type=EventChangeType.SPEC))
 assert c.change_type==ChangeType.SPEC and c.commercial_review_signal

def test_deadline_change_is_recorded_without_auto_promotion():
 c=detect_change(e(stage=ProcurementStage.TENDER),e(event_id="E2",stage=ProcurementStage.TENDER,change_type=EventChangeType.DEADLINE))
 assert c.change_type==ChangeType.DEADLINE and not c.commercial_review_signal

def test_cancellation_never_review_signal():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.CANCELLATION)); assert not c.commercial_review_signal
def test_stage_regression_is_not_misclassified_as_advance():
 c=detect_change(e(stage=ProcurementStage.CONTRACT),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.change_type==ChangeType.STAGE_REGRESSION and not c.commercial_review_signal
def test_legacy_actionable_alias_is_signal_only():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.actionable==c.commercial_review_signal
def test_cross_project_change_rejected():
 with pytest.raises(ValueError): detect_change(e(),e(event_id="E2",project_id="OTHER"))
