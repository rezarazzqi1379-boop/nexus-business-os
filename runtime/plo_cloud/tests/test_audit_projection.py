import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from audit_projection import AuditProjectionError, project_runtime_audit


def test_read_only_completion_projects_to_action_attempted_without_payload():
    event = project_runtime_audit(
        audit_id=7,
        ts="2026-08-24T08:00:00+00:00",
        action="read_only_completed",
        run_id="run-1",
        result="BRAIN-V0.2:PRJ-HYD-01:READ-ONLY-PROJECTION-VERIFIED",
        binding_digest="a" * 64,
    )
    assert event is not None
    assert event.event_type == "action_attempted"
    assert event.result_class == "passed"
    assert event.action_ref == "sha256:" + ("a" * 64)
    assert event.tags == ("plo", "read_only", "shadow")


def test_retry_budget_exhaustion_projects_as_blocked_decision():
    event = project_runtime_audit(
        audit_id=8,
        ts="2026-08-24T08:01:00+00:00",
        action="orphan_recovered",
        run_id="run-2",
        result="retry_budget_exhausted",
        binding_digest=None,
    )
    assert event is not None
    assert event.event_type == "decision_recorded"
    assert event.result_class == "blocked"


def test_native_approval_runtime_event_is_not_promoted_to_canonical_human_gate():
    event = project_runtime_audit(
        audit_id=9,
        ts="2026-08-24T08:02:00+00:00",
        action="operation_authorized",
        run_id="run-3",
        result="op-1",
        binding_digest="b" * 64,
    )
    assert event is None


def test_malformed_timestamp_and_digest_fail_closed():
    try:
        project_runtime_audit(audit_id=1, ts="2026-08-24T08:00:00", action="read_only_completed", run_id="r", result="x", binding_digest="a"*64)
        raise AssertionError("naive timestamp projected")
    except AuditProjectionError:
        pass
    try:
        project_runtime_audit(audit_id=1, ts="2026-08-24T08:00:00+00:00", action="read_only_completed", run_id="r", result="x", binding_digest="not-a-digest")
        raise AssertionError("malformed digest projected")
    except AuditProjectionError:
        pass


def main():
    tests=[v for k,v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed=0
    for test in tests:
        try:
            test(); print(test.__name__ + ": PASS")
        except Exception as exc:
            failed += 1; print(test.__name__ + f": FAIL {type(exc).__name__}: {exc}")
    print(f"\n{len(tests)-failed}/{len(tests)} audit projection tests passed")
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
