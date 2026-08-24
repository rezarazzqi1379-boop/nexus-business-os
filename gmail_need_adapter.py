from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parseaddr

from need_radar import NeedEvidence, NeedSignal


EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _mailbox(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid_gmail_address")
    display_name, address = parseaddr(value.strip())
    if not EMAIL.fullmatch(address):
        raise ValueError("invalid_gmail_address")
    # parseaddr is intentionally permissive; reject unexplained trailing/leading syntax.
    if display_name:
        expected_suffix = f"<{address}>"
        if not value.strip().endswith(expected_suffix):
            raise ValueError("invalid_gmail_address")
    elif value.strip() != address:
        raise ValueError("invalid_gmail_address")
    return address.lower()


def _timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_gmail_timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("gmail_timestamp_requires_timezone")
    return parsed.isoformat()


@dataclass(frozen=True)
class GmailMessageSnapshot:
    message_id: str
    thread_id: str
    sender: str
    recipients: tuple[str, ...]
    subject: str
    sent_at: str
    body: str
    attachment_names: tuple[str, ...] = ()

    def validate(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (
            self.message_id, self.thread_id, self.sender, self.subject
        )):
            raise ValueError("invalid_gmail_identity")
        try:
            _mailbox(self.sender)
        except ValueError as exc:
            raise ValueError("invalid_gmail_sender")
        if not self.recipients:
            raise ValueError("invalid_gmail_recipients")
        try:
            for item in self.recipients:
                _mailbox(item)
        except ValueError as exc:
            raise ValueError("invalid_gmail_recipients") from exc
        if not isinstance(self.body, str) or len(self.body) > 1_000_000:
            raise ValueError("invalid_gmail_body")
        if any(not isinstance(name, str) or not name.strip() for name in self.attachment_names):
            raise ValueError("invalid_attachment_name")
        _timestamp(self.sent_at)

    @property
    def body_sha256(self) -> str:
        self.validate()
        return hashlib.sha256(self.body.encode()).hexdigest()


@dataclass(frozen=True)
class GmailSignalProposal:
    company_id: str
    company_name: str
    company_role: str
    project_id: str
    need_hypothesis: str
    fit: str
    timing: str
    relationship: str
    evidence_classification: str
    evidence_statement: str
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()


def adapt_gmail_message(snapshot: GmailMessageSnapshot, proposal: GmailSignalProposal) -> NeedSignal:
    """Bind a reviewed proposal to Gmail evidence without treating body text as control data."""
    snapshot.validate()
    if not isinstance(proposal, GmailSignalProposal):
        raise ValueError("invalid_signal_proposal")
    if not proposal.evidence_statement.strip():
        raise ValueError("evidence_statement_required")
    source_ref = f"gmail:message:{snapshot.message_id}"
    evidence = NeedEvidence(
        evidence_id="gev_" + hashlib.sha256(source_ref.encode()).hexdigest()[:20],
        classification=proposal.evidence_classification,
        source_type="gmail",
        source_ref=source_ref,
        observed_at=_timestamp(snapshot.sent_at),
        statement=proposal.evidence_statement.strip(),
    )
    signal = NeedSignal(
        signal_id="gsig_" + hashlib.sha256((snapshot.message_id + proposal.project_id).encode()).hexdigest()[:20],
        company_id=proposal.company_id,
        company_name=proposal.company_name,
        company_role=proposal.company_role,
        project_id=proposal.project_id,
        signal_type="email_reply",
        need_hypothesis=proposal.need_hypothesis,
        fit=proposal.fit,
        timing=proposal.timing,
        relationship=proposal.relationship,
        evidence=(evidence,),
        contradictions=proposal.contradictions,
        unknowns=proposal.unknowns,
    )
    signal.validate()
    return signal
