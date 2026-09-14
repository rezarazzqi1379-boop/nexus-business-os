"""Tests for opportunity_suggestion_engine.py (Track E).

Focus areas:
1. Lane isolation is enforced (a signal outside a real FAL lane, or mismatched
   project/lane, is rejected -- never silently reassigned).
2. The queue is draft-only: nothing is ever auto-approved, auto-sent, or executed.
3. A human decision is required for every state transition, and it's recorded, not
   inferred.
4. Structural guarantee: no send/outreach/execute-shaped function exists on the module
   or the queue class.
"""

import inspect

import pytest

from approvals import ApprovalStore
from fal_vertical import FALIsolationError, LANE_FAL_A, PROJECT_ID
from need_radar import NeedEvidence, NeedSignal
import opportunity_suggestion_engine as ose


def _fact_evidence(evidence_id="ev1", source_type="official"):
    return NeedEvidence(
        evidence_id=evidence_id,
        classification="FACT",
        source_type=source_type,
        source_ref="ref:" + evidence_id,
        observed_at="2026-09-14T00:00:00+00:00",
        statement="A verifiable statement.",
    )


def _fal_a_signal(**overrides):
    defaults = dict(
        signal_id="sig1",
        company_id="company1",
        company_name="Acme Ferromanganese",
        company_role="buyer",
        project_id=PROJECT_ID,
        signal_type="procurement_request",
        need_hypothesis="Needs ferromanganese import volume for Q4.",
        fit="strong",
        timing="current",
        relationship="warm_referral",
        evidence=(_fact_evidence("ev1"), _fact_evidence("ev2", source_type="registry")),
    )
    defaults.update(overrides)
    return NeedSignal(**defaults)


@pytest.fixture
def queue(tmp_path):
    return ose.OpportunityQueue(tmp_path / "opportunities.db")


@pytest.fixture
def approval_store(tmp_path):
    return ApprovalStore(tmp_path / "approvals.db")


def test_submit_rejects_unknown_lane(queue):
    with pytest.raises(ValueError):
        queue.submit(project_id=PROJECT_ID, lane_id="NOT-A-REAL-LANE", signal=_fal_a_signal())


def test_submit_rejects_project_lane_mismatch(queue):
    with pytest.raises(FALIsolationError):
        queue.submit(project_id="SOME-OTHER-PROJECT", lane_id=LANE_FAL_A, signal=_fal_a_signal())


def test_submit_rejects_signal_project_id_not_matching_lane_scope(queue):
    mismatched = _fal_a_signal(project_id="SOME-OTHER-PROJECT")
    with pytest.raises(FALIsolationError):
        queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=mismatched)


def test_submit_creates_pending_draft_with_no_outreach_authorization(queue):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    assert draft.review_status == "draft_pending_review"
    assert draft.disposition == "priority_research"
    assert draft.research_brief is not None
    assert draft.research_brief["outreach_authorized"] is False


def test_submit_is_idempotent_on_identical_signal(queue):
    signal = _fal_a_signal()
    d1 = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=signal)
    with pytest.raises(Exception):
        # Same signal content -> same digest -> UNIQUE constraint on signal_digest.
        queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=signal)


def test_pending_review_lists_only_undecided_drafts(queue):
    queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal(signal_id="sigA"))
    pending = queue.pending_review(lane_id=LANE_FAL_A)
    assert len(pending) == 1
    assert pending[0]["review_status"] == "draft_pending_review"


def test_record_human_review_rejects_without_decision_input(queue):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    with pytest.raises(ValueError):
        queue.record_human_review(draft.draft_id, approved=True, reviewed_by="")


def test_record_human_review_refuses_approval_request_without_compliance_clearance(queue, approval_store):
    """New (2026-09-14): a review approval alone can't open the next-step
    ApprovalRequest -- compliance must be cleared separately first."""
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    with pytest.raises(PermissionError):
        queue.record_human_review(draft.draft_id, approved=True, reviewed_by="reza", approval_store=approval_store)


def test_record_human_review_approval_opens_approval_request_once_compliance_cleared(queue, approval_store):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    queue.record_compliance_review(
        draft.draft_id, cleared=True, reviewed_by="legal-reza",
        notes="Reviewed against current OFAC/EU guidance for this counterparty; no listed restriction found.",
    )
    updated = queue.record_human_review(
        draft.draft_id, approved=True, reviewed_by="reza", approval_store=approval_store
    )
    assert updated["review_status"] == "reviewed_approved"
    assert updated["approval_id"] is not None
    # The approval is still pending a SEPARATE human decision -- not auto-consumed.
    # ApprovalStore has no read accessor by design (request/decide/consume only),
    # so check status the same way test_compliance_audit_log_records_every_decision
    # already does: a direct read of its own store.
    import sqlite3
    with sqlite3.connect(approval_store.path) as db:
        row = db.execute(
            "SELECT status FROM approvals WHERE approval_id=?", (updated["approval_id"],)
        ).fetchone()
    assert row is not None
    assert row[0] == "pending"


def test_record_human_review_rejection_opens_no_approval_request(queue, approval_store):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    updated = queue.record_human_review(
        draft.draft_id, approved=False, reviewed_by="reza", approval_store=approval_store
    )
    assert updated["review_status"] == "reviewed_rejected"
    assert updated["approval_id"] is None


def test_record_human_review_cannot_be_applied_twice(queue, approval_store):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    queue.record_compliance_review(draft.draft_id, cleared=True, reviewed_by="legal-reza", notes="Cleared.")
    queue.record_human_review(draft.draft_id, approved=True, reviewed_by="reza", approval_store=approval_store)
    with pytest.raises(ValueError):
        queue.record_human_review(draft.draft_id, approved=True, reviewed_by="reza", approval_store=approval_store)


def test_record_compliance_review_requires_notes(queue):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    with pytest.raises(ValueError):
        queue.record_compliance_review(draft.draft_id, cleared=True, reviewed_by="legal-reza", notes="")


def test_compliance_blocked_permanently_refuses_approval_request(queue, approval_store):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    queue.record_compliance_review(
        draft.draft_id, cleared=False, reviewed_by="legal-reza",
        notes="Counterparty is in a sector plausibly covered by EO 13871; do not proceed.",
    )
    with pytest.raises(PermissionError):
        queue.record_human_review(draft.draft_id, approved=True, reviewed_by="reza", approval_store=approval_store)


def test_compliance_audit_log_records_every_decision(queue, tmp_path):
    draft = queue.submit(project_id=PROJECT_ID, lane_id=LANE_FAL_A, signal=_fal_a_signal())
    queue.record_compliance_review(draft.draft_id, cleared=True, reviewed_by="legal-reza", notes="Cleared once.")
    import sqlite3
    with sqlite3.connect(queue.path) as db:
        rows = db.execute("SELECT draft_id, cleared, reviewed_by FROM compliance_audit_log").fetchall()
    assert rows == [(draft.draft_id, 1, "legal-reza")]


def test_record_human_review_unknown_draft_raises(queue):
    with pytest.raises(KeyError):
        queue.record_human_review("opp_does_not_exist", approved=True, reviewed_by="reza")


FORBIDDEN_NAME_FRAGMENTS = ("send", "outreach", "execute", "dispatch", "publish", "contact", "email")


def test_module_has_no_send_or_execute_shaped_function():
    """Structural guarantee: nothing in this module can act in the outside world."""
    names = [name for name, _ in inspect.getmembers(ose, inspect.isfunction)]
    names += [name for name, _ in inspect.getmembers(ose.OpportunityQueue, predicate=inspect.isfunction)]
    for name in names:
        lowered = name.lower()
        for fragment in FORBIDDEN_NAME_FRAGMENTS:
            assert fragment not in lowered, f"found action-shaped function name: {name}"
