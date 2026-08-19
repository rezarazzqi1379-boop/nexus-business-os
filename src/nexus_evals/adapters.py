from __future__ import annotations

from typing import Any, Sequence

from .harness import Assertion, EvaluationCase


def _require_refs(evidence_refs: Sequence[str]) -> tuple[str, ...]:
    refs = tuple(ref.strip() for ref in evidence_refs if ref and ref.strip())
    if not refs:
        raise ValueError("at least one retrievable evidence_ref is required")
    return refs


def procurement_evidence_semantics_case(
    record: Any,
    *,
    expected_kind: str,
    input_ref: str,
    evidence_refs: Sequence[str],
) -> EvaluationCase:
    validation_errors = tuple(record.validate()) if hasattr(record, "validate") else ()
    evidence = getattr(record, "evidence")
    signal = getattr(record, "signal")
    outcome = getattr(record, "outcome")
    return EvaluationCase(
        case_id=f"adapter:pr1:{getattr(record, 'case_id', 'unknown')}",
        name="PR #1 evidence semantics remain explicit downstream",
        input_ref=input_ref,
        observations={"record": {"validation_errors": validation_errors, "evidence_kind": getattr(evidence, "kind", None), "evidence_summary": getattr(evidence, "summary", None), "signal_description": getattr(signal, "description", None), "outcome_result": getattr(outcome, "result", None)}},
        assertions=(
            Assertion(assertion_id="record-structurally-valid", path="record.validation_errors", operator="equals", expected=()),
            Assertion(assertion_id="epistemic-kind-preserved", path="record.evidence_kind", operator="equals", expected=expected_kind),
            Assertion(assertion_id="signal-wording-present", path="record.signal_description", operator="present"),
            Assertion(assertion_id="outcome-wording-present", path="record.outcome_result", operator="present"),
        ),
        evidence_refs=_require_refs(evidence_refs),
    )


def requirement_readiness_case(
    assessment: Any,
    *,
    input_ref: str,
    evidence_refs: Sequence[str],
    expected_blocking_ids: Sequence[str] = (),
    expected_provisional_ids: Sequence[str] = (),
    expect_discovery_ready: bool = True,
    expect_final_ready: bool = False,
) -> EvaluationCase:
    return EvaluationCase(
        case_id="adapter:pr2:requirement-readiness",
        name="PR #2 preserves provisional and unknown-blocking requirements",
        input_ref=input_ref,
        observations={
            "decision": {"ready_for_discovery": getattr(assessment, "ready_for_discovery", None), "ready_for_final_request": getattr(assessment, "ready_for_final_request", None)},
            "requirements": {"blocking_ids": tuple(getattr(assessment, "blocking_ids", ())), "provisional_ids": tuple(getattr(assessment, "provisional_ids", ()))},
            "errors": tuple(getattr(assessment, "errors", ())),
        },
        assertions=(
            Assertion(assertion_id="discovery-readiness-preserved", path="decision.ready_for_discovery", operator="equals", expected=expect_discovery_ready),
            Assertion(assertion_id="final-readiness-fails-closed", path="decision.ready_for_final_request", operator="equals", expected=expect_final_ready),
            Assertion(assertion_id="blocking-ids-preserved", path="requirements.blocking_ids", operator="equals", expected=tuple(expected_blocking_ids)),
            Assertion(assertion_id="provisional-ids-preserved", path="requirements.provisional_ids", operator="equals", expected=tuple(expected_provisional_ids)),
            Assertion(assertion_id="assessment-has-no-structural-errors", path="errors", operator="equals", expected=()),
        ),
        evidence_refs=_require_refs(evidence_refs),
    )


def action_scope_case(
    intent: Any,
    approval: Any,
    decision: Any,
    *,
    input_ref: str,
    evidence_refs: Sequence[str],
    expect_allowed: bool,
    expect_human_approval: bool,
) -> EvaluationCase:
    return EvaluationCase(
        case_id=f"adapter:pr4:{getattr(intent, 'action_id', 'unknown')}",
        name="PR #4 action-specific approval cannot drift across actions",
        input_ref=input_ref,
        observations={
            "intent": {"action_id": getattr(intent, "action_id", None), "kind": getattr(intent, "kind", None)},
            "approval": {"action_id": getattr(approval, "action_id", None) if approval is not None else None, "approved": getattr(approval, "approved", None) if approval is not None else None},
            "gate": {"allowed_now": getattr(decision, "allowed_now", None), "requires_human_approval": getattr(decision, "requires_human_approval", None), "reason": getattr(decision, "reason", None)},
        },
        assertions=(
            Assertion(assertion_id="allowed-state-matches-policy", path="gate.allowed_now", operator="equals", expected=expect_allowed),
            Assertion(assertion_id="human-gate-state-matches-policy", path="gate.requires_human_approval", operator="equals", expected=expect_human_approval),
            Assertion(assertion_id="action-id-present", path="intent.action_id", operator="present"),
            Assertion(assertion_id="gate-reason-present", path="gate.reason", operator="present"),
        ),
        evidence_refs=_require_refs(evidence_refs),
    )
