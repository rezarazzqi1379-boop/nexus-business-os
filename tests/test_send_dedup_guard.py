from datetime import datetime, timezone, timedelta

from nexus_core.send_dedup_guard import ThreadMessageState, evaluate_send_against_thread


def dt(minutes: int) -> datetime:
    return datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=minutes)


def test_blocks_when_newer_sent_message_exists():
    decision = evaluate_send_against_thread(
        draft_created_at=dt(0),
        thread_id="t1",
        messages=(ThreadMessageState("m1", "t1", dt(10), True),),
    )
    assert decision.allowed is False
    assert decision.reason == "newer_sent_message_exists"
    assert decision.blocking_message_id == "m1"


def test_allows_when_only_older_or_unsent_messages_exist():
    decision = evaluate_send_against_thread(
        draft_created_at=dt(10),
        thread_id="t1",
        messages=(
            ThreadMessageState("m1", "t1", dt(0), True),
            ThreadMessageState("m2", "t1", dt(20), False),
        ),
    )
    assert decision.allowed is True


def test_other_thread_does_not_block():
    decision = evaluate_send_against_thread(
        draft_created_at=dt(0),
        thread_id="t1",
        messages=(ThreadMessageState("m1", "t2", dt(10), True),),
    )
    assert decision.allowed is True


def test_duplicate_message_ids_fail_closed():
    msg = ThreadMessageState("m1", "t1", dt(1), False)
    decision = evaluate_send_against_thread(
        draft_created_at=dt(0), thread_id="t1", messages=(msg, msg)
    )
    assert decision.allowed is False
    assert decision.reason == "duplicate_message_id"


def test_naive_draft_timestamp_fails_closed():
    decision = evaluate_send_against_thread(
        draft_created_at=datetime(2026, 8, 20),
        thread_id="t1",
        messages=(),
    )
    assert decision.allowed is False
    assert decision.reason == "naive_draft_timestamp"
