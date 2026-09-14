"""Opportunity Suggestion Engine (Track E).

This completes the item CURRENT_STATE.md lists as "designed, not yet built":
a draft-only opportunity queue with a human approval gate that never auto-sends.

It does not reimplement evidence grading, lane isolation, or approvals -- those
already exist and are reused as-is:
  - need_radar.py: NeedSignal validation, evidence-graded disposition, research briefs
    (every research_brief() carries outreach_authorized=False -- unconditionally).
  - fal_vertical.py: FAL-A/FAL-B lane isolation (a signal must validate against a real,
    known lane; cross-lane/cross-project contamination is rejected).
  - approvals.py: single-use, exact-scope human approval store.

What this module adds is the missing glue: a persistent draft queue that takes a
lane-scoped NeedSignal, runs it through need_radar's assessment, and stores the result
as a draft a human reviews -- structurally incapable of sending anything itself. There
is deliberately no send/execute/outreach function anywhere in this module. The only
state transitions available are: draft created -> human marks reviewed (approved/
rejected) -> (if approved and disposition warranted it) an ApprovalRequest is opened
for the *next* human-gated step. Nothing here is ever consumed automatically.

Compliance gate (added 2026-09-14): a web search while preparing NEXUS's networking
proposals turned up that US Executive Order 13871 names "Iron, Steel, Aluminum, and
Copper Sectors of Iran" and that EU reporting describes a reinstated steel/metals trade
ban with Iran in 2026 -- both plausibly touch a ferroalloys (steel-input) vertical like
FAL-A/FAL-B, though the exact legal scope needs a real sanctions/export-control lawyer,
not this code. So every draft here starts `compliance_status="UNREVIEWED"`, and
`record_human_review(approved=True)` refuses to open the next-step ApprovalRequest
until a separate human has called `record_compliance_review(cleared=True, ...)` for
that draft. This is evidence-recording only -- it does not itself determine legality.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from approvals import ApprovalRequest, ApprovalStore
from fal_vertical import FALIsolationError, assert_lane_scope
from need_radar import NeedAssessment, NeedSignal, assess_need, research_brief

# Dispositions that justify opening a human approval request for continued research
# effort (never for outreach -- outreach_authorized is hardcoded False in need_radar).
RESEARCH_WORTHY_DISPOSITIONS = frozenset({"priority_research", "research", "supply_research"})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OpportunityDraft:
    draft_id: str
    project_id: str
    lane_id: str
    signal_id: str
    signal_digest: str
    disposition: str
    reasons: tuple[str, ...]
    next_safe_action: str
    research_brief: Optional[dict] = None
    review_status: str = "draft_pending_review"
    approval_id: Optional[str] = None
    created_at: str = ""
    compliance_status: str = "UNREVIEWED"


class OpportunityQueue:
    """Persistent, human-reviewed queue of opportunity drafts.

    Structural guarantee: this class has no method that contacts anyone, publishes
    anything, or marks a draft as acted upon without a human-supplied decision. Review
    is recorded, never inferred.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            with db:
                db.execute("""
                CREATE TABLE IF NOT EXISTS opportunity_drafts (
                    draft_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, lane_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL, signal_digest TEXT NOT NULL, disposition TEXT NOT NULL,
                    reasons_json TEXT NOT NULL, next_safe_action TEXT NOT NULL,
                    research_brief_json TEXT, review_status TEXT NOT NULL,
                    approval_id TEXT, created_at TEXT NOT NULL, reviewed_at TEXT, reviewed_by TEXT,
                    compliance_status TEXT NOT NULL DEFAULT 'UNREVIEWED',
                    compliance_reviewed_at TEXT, compliance_reviewed_by TEXT, compliance_notes TEXT,
                    UNIQUE(signal_digest)
                )
            """)
                db.execute("""
                CREATE TABLE IF NOT EXISTS compliance_audit_log (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT, draft_id TEXT NOT NULL,
                    cleared INTEGER NOT NULL, reviewed_by TEXT NOT NULL, notes TEXT, recorded_at TEXT NOT NULL
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def submit(self, *, project_id: str, lane_id: str, signal: NeedSignal) -> OpportunityDraft:
        """Validate the signal against the real FAL lane, assess it via need_radar's
        evidence discipline, and store it as a pending draft. Raises FALIsolationError
        if the signal doesn't belong to a real, matching lane -- never silently
        reassigns it to one."""
        assert_lane_scope(project_id=project_id, lane_id=lane_id)
        if signal.project_id != project_id:
            raise FALIsolationError("signal_project_id_does_not_match_lane_scope")

        assessment: NeedAssessment = assess_need(signal)
        brief = None
        if assessment.disposition in RESEARCH_WORTHY_DISPOSITIONS:
            brief = research_brief(assessment)
            assert brief["outreach_authorized"] is False  # structural invariant, not optional

        draft = OpportunityDraft(
            draft_id="opp_" + signal.digest[:24],
            project_id=project_id,
            lane_id=lane_id,
            signal_id=signal.signal_id,
            signal_digest=signal.digest,
            disposition=assessment.disposition,
            reasons=tuple(assessment.reasons),
            next_safe_action=assessment.next_safe_action,
            research_brief=brief,
            review_status="draft_pending_review",
            created_at=utc_now_iso(),
        )
        with closing(self._connect()) as db:
            with db:
                db.execute(
                    "INSERT INTO opportunity_drafts "
                    "(draft_id, project_id, lane_id, signal_id, signal_digest, disposition, "
                    "reasons_json, next_safe_action, research_brief_json, review_status, "
                    "approval_id, created_at, reviewed_at, reviewed_by, compliance_status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (draft.draft_id, draft.project_id, draft.lane_id, draft.signal_id,
                     draft.signal_digest, draft.disposition,
                     json.dumps(draft.reasons), draft.next_safe_action,
                     json.dumps(draft.research_brief) if draft.research_brief else None,
                     draft.review_status, None, draft.created_at, None, None,
                     draft.compliance_status),
                )
        return draft

    def get(self, draft_id: str) -> Optional[dict]:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM opportunity_drafts WHERE draft_id=?", (draft_id,)).fetchone()
            return dict(row) if row is not None else None

    def pending_review(self, *, lane_id: Optional[str] = None) -> list[dict]:
        """Everything still waiting on a human -- this is 'the queue' a person reads."""
        with closing(self._connect()) as db:
            if lane_id:
                rows = db.execute(
                    "SELECT * FROM opportunity_drafts WHERE review_status=? AND lane_id=? ORDER BY created_at",
                    ("draft_pending_review", lane_id),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM opportunity_drafts WHERE review_status=? ORDER BY created_at",
                    ("draft_pending_review",),
                ).fetchall()
            return [dict(r) for r in rows]

    def record_compliance_review(self, draft_id: str, *, cleared: bool, reviewed_by: str,
                                  notes: str) -> dict:
        """Record a human's sanctions/export-control compliance decision for a draft.
        This does not determine legality itself -- it only records that a named human
        made a call, with their reasoning, in an append-only audit log. `cleared=False`
        permanently blocks the draft from ever opening a research ApprovalRequest."""
        if not reviewed_by.strip():
            raise ValueError("invalid_reviewer")
        if not notes.strip():
            raise ValueError("compliance_notes_required")  # a bare yes/no isn't an audit trail
        current = self.get(draft_id)
        if current is None:
            raise KeyError("unknown_draft")
        new_status = "CLEARED" if cleared else "BLOCKED"
        now = utc_now_iso()
        with closing(self._connect()) as db:
            with db:
                db.execute(
                    "UPDATE opportunity_drafts SET compliance_status=?, compliance_reviewed_at=?, "
                    "compliance_reviewed_by=?, compliance_notes=? WHERE draft_id=?",
                    (new_status, now, reviewed_by, notes, draft_id),
                )
                db.execute(
                    "INSERT INTO compliance_audit_log (draft_id, cleared, reviewed_by, notes, recorded_at) "
                    "VALUES (?,?,?,?,?)",
                    (draft_id, int(cleared), reviewed_by, notes, now),
                )
        return self.get(draft_id)  # type: ignore[return-value]

    def record_human_review(self, draft_id: str, *, approved: bool, reviewed_by: str,
                             approval_store: Optional[ApprovalStore] = None) -> dict:
        """Record a human's decision on a draft. This NEVER performs the researched
        action itself -- if approved and the draft warrants continued research effort,
        it opens a fresh ApprovalRequest in the existing approvals store for that next
        step, which still requires a separate human decision to consume. That next-step
        request is refused (PermissionError) unless compliance_status is already
        "CLEARED" via record_compliance_review -- reviewing a draft does not itself
        clear it for compliance."""
        if not reviewed_by.strip():
            raise ValueError("invalid_reviewer")
        current = self.get(draft_id)
        if current is None:
            raise KeyError("unknown_draft")
        if current["review_status"] != "draft_pending_review":
            raise ValueError("draft_not_pending_review")

        new_status = "reviewed_approved" if approved else "reviewed_rejected"
        approval_id = None
        wants_approval_request = (
            approved and current["disposition"] in RESEARCH_WORTHY_DISPOSITIONS and approval_store is not None
        )
        if wants_approval_request:
            if current["compliance_status"] == "BLOCKED":
                raise PermissionError(f"draft {draft_id} is compliance-BLOCKED; cannot proceed")
            if current["compliance_status"] != "CLEARED":
                raise PermissionError(
                    f"draft {draft_id} has compliance_status={current['compliance_status']!r}; "
                    "call record_compliance_review(cleared=True, ...) first"
                )
            approval_id = approval_store.request(ApprovalRequest(
                project_id=current["project_id"],
                action="proceed_with_research_brief",
                target=current["draft_id"],
                parameters={"signal_digest": current["signal_digest"]},
                requested_by=reviewed_by,
            ))

        with closing(self._connect()) as db:
            with db:
                changed = db.execute(
                    "UPDATE opportunity_drafts SET review_status=?, approval_id=?, "
                    "reviewed_at=?, reviewed_by=? WHERE draft_id=? AND review_status='draft_pending_review'",
                    (new_status, approval_id, utc_now_iso(), reviewed_by, draft_id),
                ).rowcount
                if changed != 1:
                    raise ValueError("draft_not_pending_review")
        return self.get(draft_id)  # type: ignore[return-value]
