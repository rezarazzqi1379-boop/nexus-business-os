from datetime import datetime,timezone
import pytest
from procurement_event_chain import *
from commercial_change_detector import *
T=datetime(2026,1,1,tzinfo=timezone.utc)
def e(**kw):
 d=dict(process_id="P",event_id="E1",project_id="NEXUS-BUSINESS-OS",buyer_id="B",stage=ProcurementStage.PLANNING,source_locator="u",observed_at=T,event_at=T); d.update(kw); return ProcurementEvent(**d)

def test_tender_stage_advance_is_review_signal_not_action_authority():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.change_type==ChangeType.STAGE_ADVANCE and c.commercial_review_signal
def test_supplier_change_detected():
 c=detect_change(e(stage=ProcurementStage.AWARD,supplier_id="A"),e(event_id="E2",stage=ProcurementStage.CONTRACT,supplier_id="B")); assert c.change_type==ChangeType.SUPPLIER_CHANGE and c.commercial_review_signal
def test_cancellation_never_review_signal():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.CANCELLATION)); assert not c.commercial_review_signal
def test_stage_regression_is_not_misclassified_as_advance():
 c=detect_change(e(stage=ProcurementStage.CONTRACT),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.change_type==ChangeType.STAGE_REGRESSION and not c.commercial_review_signal
def test_legacy_actionable_alias_is_signal_only():
 c=detect_change(e(),e(event_id="E2",stage=ProcurementStage.TENDER)); assert c.actionable==c.commercial_review_signal
def test_cross_project_change_rejected():
 with pytest.raises(ValueError): detect_change(e(),e(event_id="E2",project_id="OTHER"))
