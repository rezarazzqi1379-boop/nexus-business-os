from nexus_core.retry_budget import RetryPolicy, decide_retry, half_open_probe


def test_transient_failure_gets_bounded_backoff():
    d = decide_retry(failure="transient", attempt=1, consecutive_failures=1)
    assert d.retry is True
    assert d.delay_ms > 0
    assert d.circuit == "closed"


def test_auth_failure_never_retries_blindly():
    d = decide_retry(failure="auth", attempt=1, consecutive_failures=1)
    assert d.retry is False
    assert d.circuit == "open"


def test_failure_threshold_opens_circuit():
    d = decide_retry(failure="timeout", attempt=2, consecutive_failures=3)
    assert d.retry is False
    assert d.reason == "failure_threshold_reached"


def test_retry_budget_exhaustion_opens_circuit():
    p = RetryPolicy(max_attempts=2)
    d = decide_retry(failure="rate_limit", attempt=2, consecutive_failures=1, policy=p)
    assert d.retry is False
    assert d.reason == "retry_budget_exhausted"


def test_half_open_probe_controls_recovery():
    assert half_open_probe(probe_succeeded=True).circuit == "closed"
    assert half_open_probe(probe_succeeded=False).circuit == "open"
