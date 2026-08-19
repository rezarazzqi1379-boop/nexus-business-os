from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class ThreadMessageState:
    message_id: str
    thread_id: str
    sent_at: datetime
    is_sent: bool


@dataclass(frozen=True)
class SendGuardDecision:
    allowed: bool
    reason: str
    blocking_message_id: str | None = None


def evaluate_send_against_thread(
    *,
    draft_created_at: datetime,
    thread_id: str,
    messages: Iterable[ThreadMessageState],
) -> SendGuardDecision:
    """Block a send when the same thread already contains a newer SENT message.

    The guard is intentionally chronology-based and fail-closed on malformed
    state. It does not authorize a send; it only prevents stale-draft replay.
    """
    if not thread_id.strip():
        return SendGuardDecision(False, "invalid_thread_id")
    if draft_created_at.tzinfo is None or draft_created_at.utcoffset() is None:
        return SendGuardDecision(False, "naive_draft_timestamp")

    newest_blocker: ThreadMessageState | None = None
    seen_ids: set[str] = set()
    for msg in messages:
        if not isinstance(msg, ThreadMessageState):
            return SendGuardDecision(False, "invalid_message_state")
        if not msg.message_id.strip() or not msg.thread_id.strip():
            return SendGuardDecision(False, "invalid_message_state")
        if msg.message_id in seen_ids:
            return SendGuardDecision(False, "duplicate_message_id")
        seen_ids.add(msg.message_id)
        if msg.sent_at.tzinfo is None or msg.sent_at.utcoffset() is None:
            return SendGuardDecision(False, "naive_message_timestamp")
        if msg.thread_id != thread_id or not msg.is_sent:
            continue
        if msg.sent_at <= draft_created_at:
            continue
        if newest_blocker is None or msg.sent_at > newest_blocker.sent_at:
            newest_blocker = msg

    if newest_blocker is not None:
        return SendGuardDecision(
            False,
            "newer_sent_message_exists",
            newest_blocker.message_id,
        )
    return SendGuardDecision(True, "no_newer_sent_message")
