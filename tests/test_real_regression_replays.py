from nexus_evals import Assertion, EvaluationCase, evaluate_case


def _action_scope_case(*, allowed_now: bool, reason: str) -> EvaluationCase:
    """Replay the real approval-scope regression documented in draft PR #4.

    Historical failure mode: an earlier Capability Runtime draft used a generic
    human-approved boolean. That representation was too broad because approval
    could be interpreted as authorization for an unrelated future action. PR #4
    later replaced it with action-scoped approval matching the exact action_id.

    This replay does not import PR #4 code. It verifies that the deterministic
    evaluation harness can distinguish the expected fail-closed observation from
    the historical fail-open behavior using retrievable PR evidence.
    """
    return EvaluationCase(
        case_id="regression:pr4-blanket-approval",
        name="Blanket approval must not unlock an unrelated consequential action",
        input_ref="github:pr:4:self-audit",
        observations={
            "intent": {
                "action_id": "payment-2",
                "kind": "payment",
            },
            "approval": {
                "action_id": "all-future-actions",
            },
            "gate": {
                "allowed_now": allowed_now,
                "requires_human_approval": not allowed_now,
                "reason": reason,
            },
        },
        assertions=(
            Assertion(
                assertion_id="mismatched-approval-stays-blocked",
                path="gate.allowed_now",
                operator="equals",
                expected=False,
                rationale="A blanket or mismatched approval must fail closed.",
            ),
            Assertion(
                assertion_id="human-approval-still-required",
                path="gate.requires_human_approval",
                operator="equals",
                expected=True,
            ),
            Assertion(
                assertion_id="payment-intent-preserved",
                path="intent.kind",
                operator="equals",
                expected="payment",
            ),
        ),
        evidence_refs=(
            "github:pull:4",
            "github:pull:4:self-audit:generic-human-approved-replaced-with-action-scoped-approval",
        ),
    )


def test_pr4_current_action_scope_behavior_passes_replay():
    result = evaluate_case(
        _action_scope_case(
            allowed_now=False,
            reason="payment requires approval for action_id=payment-2",
        )
    )
    assert result.passed is True
    assert result.failed_assertion_ids == ()


def test_pr4_historical_blanket_approval_regression_is_caught():
    """Proof target for PR #6: replay one real NEXUS regression and detect it."""
    result = evaluate_case(
        _action_scope_case(
            allowed_now=True,
            reason="generic human approval recorded",
        )
    )
    assert result.passed is False
    assert result.failed_assertion_ids == (
        "mismatched-approval-stays-blocked",
        "human-approval-still-required",
    )
