import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from plo_core import IdempotencyConflictError, PLOStore
from control_bridge import ExecutionClass, ExecutionEnvelope, EnvelopeError, enqueue_from_control, immutable_binding_digest, validate_envelope

D = "a" * 64


def env(**kw):
    base = dict(project_id="PRJ-HYD-01", task_id="shadow-research", decision_ref="DEC-1", control_ref="FORGE-1", action_digest=D, idempotency_key="idem-1", execution_class=ExecutionClass.SHADOW)
    base.update(kw)
    return ExecutionEnvelope(**base)


def test_shadow_valid_and_cannot_have_external_effect():
    validate_envelope(env())
    try:
        validate_envelope(env(external_effect=True))
        raise AssertionError("shadow external effect accepted")
    except EnvelopeError:
        pass


def test_shadow_cannot_smuggle_approval_ref():
    try:
        validate_envelope(env(exact_approval_ref="APR-1"))
        raise AssertionError("shadow approval reference accepted")
    except EnvelopeError:
        pass


def test_consequential_requires_upstream_exact_approval_reference_at_schema_level():
    try:
        validate_envelope(env(execution_class=ExecutionClass.CONSEQUENTIAL, external_effect=True))
        raise AssertionError("consequential envelope without approval ref accepted")
    except EnvelopeError:
        pass
    validate_envelope(env(execution_class=ExecutionClass.CONSEQUENTIAL, external_effect=True, exact_approval_ref="APR-EXACT-1"))


def test_digest_is_strict_sha256_hex():
    for bad in ("", "A" * 64, "a" * 63, "z" * 64):
        try:
            validate_envelope(env(action_digest=bad))
            raise AssertionError("bad digest accepted")
        except EnvelopeError:
            pass


def test_binding_digest_is_deterministic_and_approval_token_independent():
    a = env(execution_class=ExecutionClass.CONSEQUENTIAL, external_effect=True, exact_approval_ref="APR-1")
    b = env(execution_class=ExecutionClass.CONSEQUENTIAL, external_effect=True, exact_approval_ref="APR-2")
    assert immutable_binding_digest(a) == immutable_binding_digest(b)


def test_bridge_only_enqueues_and_preserves_idempotency():
    with tempfile.TemporaryDirectory() as td:
        s = PLOStore(os.path.join(td, "p.db"))
        e = env()
        a = enqueue_from_control(s, e)
        b = enqueue_from_control(s, e)
        assert a == b
        assert s.metrics()["pending"] == 1


def test_same_idempotency_key_with_changed_action_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        s = PLOStore(os.path.join(td, "p.db"))
        enqueue_from_control(s, env())
        changed = env(action_digest="b" * 64)
        try:
            enqueue_from_control(s, changed)
            raise AssertionError("idempotency key rebound to changed action")
        except IdempotencyConflictError:
            pass
        assert s.metrics()["pending"] == 1


def test_same_idempotency_key_with_changed_project_or_decision_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        s = PLOStore(os.path.join(td, "p.db"))
        enqueue_from_control(s, env())
        for changed in (env(project_id="PRJ-HTL-01"), env(decision_ref="DEC-2"), env(control_ref="FORGE-2")):
            try:
                enqueue_from_control(s, changed)
                raise AssertionError("idempotency key rebound across immutable control context")
            except IdempotencyConflictError:
                pass


def test_legacy_unbound_key_cannot_be_silently_adopted_by_control_bridge():
    with tempfile.TemporaryDirectory() as td:
        s = PLOStore(os.path.join(td, "p.db"))
        s.enqueue("legacy", "idem-1")
        try:
            enqueue_from_control(s, env())
            raise AssertionError("legacy unbound idempotency key silently adopted")
        except IdempotencyConflictError:
            pass


def test_consequential_control_intake_is_disabled_even_with_textual_approval_ref():
    with tempfile.TemporaryDirectory() as td:
        s = PLOStore(os.path.join(td, "p.db"))
        e = env(execution_class=ExecutionClass.CONSEQUENTIAL, external_effect=True, exact_approval_ref="APR-EXACT-1", idempotency_key="idem-2")
        try:
            enqueue_from_control(s, e)
            raise AssertionError("consequential control intake enabled before approval authority consolidation")
        except EnvelopeError:
            pass
        assert s.metrics()["pending"] == 0


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for test in tests:
        try:
            test(); print(test.__name__ + ": PASS")
        except Exception as exc:
            failed += 1; print(test.__name__ + f": FAIL {type(exc).__name__}: {exc}")
    print(f"\n{len(tests)-failed}/{len(tests)} control bridge tests passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
