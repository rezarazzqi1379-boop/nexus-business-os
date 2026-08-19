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


def _valid_aware_datetime(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def evaluate_send_against_thread(
    *,
    draft_created_at: datetime,
    thread_id: str,
    messages: Iterable[ThreadMessageState],
) -> SendGuardDecision:
    """Block a send when the same thread already contains a newer SENT message.

    This is a prevention guard only: an allow result is never authorization to send.
    Runtime inputs are validated fail-closed because type hints are not enforcement.
    """
    if not isinstance(thread_id, str) or not thread_id.strip() or thread_id != thread_id.strip():
        return SendGuardDecision(False, "invalid_thread_id")
    if not _valid_aware_datetime(draft_created_at):
        return SendGuardDecision(False, "invalid_draft_timestamp")

    try:
        iterator = iter(messages)
    except TypeError:
        return SendGuardDecision(False, "invalid_messages")

    newest_blocker: ThreadMessageState | None = None
    seen_ids: set[str] = set()
    for msg in iterator:
        if not isinstance(msg, ThreadMessageState):
            return SendGuardDecision(False, "invalid_message_state")
        if (
            not isinstance(msg.message_id, str)
            or not msg.message_id.strip()
            or msg.message_id != msg.message_id.strip()
            or not isinstance(msg.thread_id, str)
            or not msg.thread_id.strip()
            or msg.thread_id != msg.thread_id.strip()
            or not isinstance(msg.is_sent, bool)
            or not _valid_aware_datetime(msg.sent_at)
        ):
            return SendGuardDecision(False, "invalid_message_state")
        if msg.message_id in seen_ids:
            return SendGuardDecision(False, "duplicate_message_id")
        seen_ids.add(msg.message_id)
        if msg.thread_id != thread_id or msg.is_sent is not True:
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
