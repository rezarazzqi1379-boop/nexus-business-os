import os, sys, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from postgres_store import PostgresPLOStore, PostgresApprovalError, PostgresOwnershipError

DSN = os.environ["NEXUS_PLO_DATABASE_URL"]


def fresh():
    s = PostgresPLOStore(DSN)
    s.migrate()
    s.reset_for_tests()
    return s


def test_idempotent_enqueue():
    s = fresh()
    a = s.enqueue("task", "same-key")
    b = s.enqueue("task", "same-key")
    assert a == b


def test_two_workers_only_one_claims():
    s = fresh()
    rid = s.enqueue("task", "claim-key")
    results = []
    barrier = threading.Barrier(3)
    def worker(name):
        barrier.wait()
        results.append((name, PostgresPLOStore(DSN).claim_next(name, 30)))
    t1 = threading.Thread(target=worker, args=("A",))
    t2 = threading.Thread(target=worker, args=("B",))
    t1.start(); t2.start(); barrier.wait(); t1.join(); t2.join()
    claimed = [r for _, r in results if r is not None]
    assert len(claimed) == 1, results
    assert claimed[0]["run_id"] == rid


def test_expired_lease_cannot_renew():
    s = fresh(); rid = s.enqueue("task", "lease-key"); c = s.claim_next("A", -1)
    try:
        s.renew_lease(rid, c["_lease_token"], "A")
        raise AssertionError("expired lease renewed")
    except PostgresOwnershipError:
        pass


def test_expired_lease_cannot_authorize():
    s = fresh(); rid = s.enqueue("send", "expired-auth", True); c = s.claim_next("A", -1)
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    try:
        s.authorize_operation(rid, "op-expired", "send:a", c["_lease_token"], "A")
        raise AssertionError("expired lease authorized")
    except PostgresOwnershipError:
        pass


def test_expired_lease_cannot_record_intent():
    s = fresh(); rid = s.enqueue("send", "intent-gap", True); c = s.claim_next("A", 30)
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    tok = s.authorize_operation(rid, "op-gap", "send:a", c["_lease_token"], "A")
    s.renew_lease(rid, c["_lease_token"], "A", -1)
    try:
        s.record_intent(rid, "op-gap", tok, c["_lease_token"], "A")
        raise AssertionError("expired lease recorded intent")
    except PostgresOwnershipError:
        pass


def test_stale_approval_version_blocked():
    s = fresh(); rid = s.enqueue("send", "stale-key", True)
    aid = s.request_approval(rid, "send:a"); c = s.claim_next("A"); s.decide_approval(aid, "approved")
    try:
        s.authorize_operation(rid, "op-stale", "send:a", c["_lease_token"], "A")
        raise AssertionError("stale approval authorized")
    except PostgresApprovalError:
        pass


def test_exact_scope_approval_before_intent():
    s = fresh(); rid = s.enqueue("send", "approve-key", True); c = s.claim_next("A")
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    try:
        s.authorize_operation(rid, "op-wrong", "send:b", c["_lease_token"], "A")
        raise AssertionError("wrong scope authorized")
    except PostgresApprovalError:
        pass
    tok = s.authorize_operation(rid, "op-good", "send:a", c["_lease_token"], "A")
    s.record_intent(rid, "op-good", tok, c["_lease_token"], "A")


def test_mark_executed_requires_intent():
    s = fresh(); rid = s.enqueue("send", "order", True); c = s.claim_next("A")
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    s.authorize_operation(rid, "op-order", "send:a", c["_lease_token"], "A")
    try:
        s.mark_executed("op-order")
        raise AssertionError("executed without intent")
    except PostgresApprovalError:
        pass


def test_approval_single_use():
    s = fresh(); rid = s.enqueue("send", "single-use", True); c = s.claim_next("A")
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    s.authorize_operation(rid, "op-one", "send:a", c["_lease_token"], "A")
    try:
        s.authorize_operation(rid, "op-two", "send:a", c["_lease_token"], "A")
        raise AssertionError("approval reused")
    except PostgresApprovalError:
        pass


def test_orphan_recovery_and_fencing():
    s = fresh(); rid = s.enqueue("task", "orphan"); old = s.claim_next("A", -1)
    recovered = s.recover_orphans(); assert rid in recovered
    new = s.claim_next("B", 30); assert new and new["run_id"] == rid
    try:
        s.renew_lease(rid, old["_lease_token"], "A")
        raise AssertionError("stale worker revived")
    except PostgresOwnershipError:
        pass


def test_duplicate_execution_metric():
    s = fresh(); rid = s.enqueue("send", "dup", True); c = s.claim_next("A")
    aid = s.request_approval(rid, "send:a"); s.decide_approval(aid, "approved")
    tok = s.authorize_operation(rid, "op-dup", "send:a", c["_lease_token"], "A")
    s.record_intent(rid, "op-dup", tok, c["_lease_token"], "A")
    s.mark_executed("op-dup"); s.mark_executed("op-dup")
    assert s.metrics()["duplicate_execution_count"] == 1


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for test in tests:
        try:
            test(); print(test.__name__ + ": PASS")
        except Exception as exc:
            failed += 1; print(test.__name__ + f": FAIL {type(exc).__name__}: {exc}")
    print(f"\n{len(tests)-failed}/{len(tests)} PostgreSQL integration tests passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
